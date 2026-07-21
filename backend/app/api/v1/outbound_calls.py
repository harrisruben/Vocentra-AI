from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.models import Organization, User, Customer, Call
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.services import get_voice_provider
from app.voice.session_manager import SessionManager
from app.voice.transcripts.transcripts import broadcast_active_calls
from app.core.logger import logger
import hashlib

router = APIRouter(prefix="/calls", tags=["Outbound Calls"])

class OutboundCallPayload(BaseModel):
    customer_phone: str
    customer_name: Optional[str] = None

def get_int_id(vapi_call_id: str) -> int:
    if not vapi_call_id:
        return 0
    if isinstance(vapi_call_id, int):
        return vapi_call_id
    if vapi_call_id.isdigit():
        return int(vapi_call_id)
    return int(hashlib.md5(vapi_call_id.encode('utf-8')).hexdigest()[:6], 16)

@router.post("/outbound", response_model=StandardResponse[dict])
async def trigger_outbound_call(
    payload: OutboundCallPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    logger.info(f"Outbound API: Starting outbound call to {payload.customer_phone} for org={org_id}")

    # 1. Load Organization Settings
    org_res = await db.execute(select(Organization).filter(Organization.id == org_id))
    org = org_res.scalar()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    voice_provider = get_voice_provider()

    # Resolve active Vapi Assistant ID
    assistant_id = org.vapi_assistant_id
    if not assistant_id or assistant_id == "vapi_assistant_mock_id":
        try:
            assistants = await voice_provider.get_assistants()
            if assistants:
                assistant_id = assistants[0].get("id")
        except Exception as e:
            logger.error(f"Outbound API: Error discovering assistant: {str(e)}")
    
    if not assistant_id:
        assistant_id = "vapi_assistant_mock_id"

    # 2. Get or create Customer
    cust_res = await db.execute(select(Customer).filter(Customer.phone == payload.customer_phone, Customer.organization_id == org_id))
    customer = cust_res.scalar()
    if not customer:
        customer = Customer(
            name=payload.customer_name or f"Lead {payload.customer_phone[-4:]}",
            phone=payload.customer_phone,
            organization_id=org_id
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

    # 3. Trigger call via Voice Provider
    metadata = {
        "org_id": org_id,
        "customer_id": customer.id,
        "triggered_by": current_user.email
    }

    # Resolve dynamic Vapi Phone Number ID associated with +19843712375
    phone_number_id = None
    try:
        phones = await voice_provider.get_phone_numbers()
        for p in phones:
            p_num = p.get("number", "")
            clean_p = "".join(c for c in p_num if c.isdigit() or c == "+")
            clean_target = "".join(c for c in "+19843712375" if c.isdigit() or c == "+")
            if clean_p == clean_target:
                phone_number_id = p.get("id")
                break
        if not phone_number_id and phones:
            phone_number_id = phones[0].get("id")
    except Exception as e:
        logger.error(f"Outbound API: Error resolving Vapi phone number ID: {str(e)}")

    vapi_res = await voice_provider.start_call(
        assistant_id=assistant_id,
        phone_number_id=phone_number_id,
        customer_number=payload.customer_phone,
        metadata=metadata
    )

    vapi_call_id = vapi_res.get("id")

    # 4. Initialize session manager transient cache
    state = SessionManager.get_session(vapi_call_id)
    state["last_utterance"] = "Calling lead... Connecting voice session."
    state["customer_name"] = customer.name
    state["customer_phone"] = customer.phone
    state["active_intent"] = "Outbound Call"

    # Broadcast updates to WebSockets
    await broadcast_active_calls(org_id, db)

    return StandardResponse(
        success=True,
        message="Outbound call session successfully initiated.",
        data={
            "vapi_call_id": vapi_call_id,
            "int_call_id": get_int_id(vapi_call_id)
        }
    )

@router.post("/{call_id}/end", response_model=StandardResponse[dict])
async def end_active_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    logger.info(f"Outbound API: Terminating active call {call_id} from org {org_id}")

    voice_provider = get_voice_provider()
    success = await voice_provider.end_call(call_id)
    if not success:
        logger.warn(f"Failed to end call {call_id} on Vapi, clearing local cache.")

    SessionManager.clear_session(call_id)
    await broadcast_active_calls(org_id, db)

    return StandardResponse(
        success=True,
        message=f"Call {call_id} terminated successfully.",
        data={"success": True}
    )
