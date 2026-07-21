from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import Call, Customer, Organization, User
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.voice.session_manager import SessionManager
from app.voice.transcripts.transcripts import broadcast_active_calls
from app.core.logger import logger
from app.services.vapi_service import VapiService
from pydantic import BaseModel
from typing import Optional
import datetime
import hashlib
from sqlalchemy.future import select

def get_int_id(vapi_call_id: str) -> int:
    if not vapi_call_id:
        return 0
    if isinstance(vapi_call_id, int):
        return vapi_call_id
    if vapi_call_id.isdigit():
        return int(vapi_call_id)
    return int(hashlib.md5(vapi_call_id.encode('utf-8')).hexdigest()[:6], 16)

router = APIRouter(prefix="/calls", tags=["Calls"])

class CallStartPayload(BaseModel):
    vapi_call_id: str
    twilio_call_id: Optional[str] = None
    customer_phone: str

class CallEndPayload(BaseModel):
    vapi_call_id: str
    twilio_call_id: Optional[str] = None
    duration: int
    recording_url: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    cost: float = 0.0

class CallTranscriptPayload(BaseModel):
    vapi_call_id: str
    text: str
    role: str  # user, assistant

class CallStatusPayload(BaseModel):
    vapi_call_id: str
    status: str  # ringing, connected, completed, failed

@router.post("/start", response_model=StandardResponse[dict])
async def start_call(payload: CallStartPayload, db: AsyncSession = Depends(get_db)):
    logger.info(f"Calls API: Starting call {payload.vapi_call_id} for {payload.customer_phone}")
    
    # 1. Resolve organization (default sandbox org)
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalar()
    if not org:
        org = Organization(name="Default Sandbox Org")
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
    # 2. Resolve customer
    cust_res = await db.execute(select(Customer).filter(Customer.phone == payload.customer_phone))
    customer = cust_res.scalar()
    if not customer:
        customer = Customer(
            name=f"Caller {payload.customer_phone[-4:]}" if len(payload.customer_phone) > 4 else "Caller",
            phone=payload.customer_phone,
            organization_id=org.id
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        
    # Initialize session state cache
    session_id = payload.vapi_call_id
    state = SessionManager.get_session(session_id)
    state["last_utterance"] = "Call connected. Ready for conversation."
    
    # Broadcast live update
    await broadcast_active_calls(org.id, db)
    
    return StandardResponse(
        success=True,
        message="Call session successfully started",
        data={"call_id": get_int_id(payload.vapi_call_id), "session_id": session_id}
    )

@router.post("/end", response_model=StandardResponse[dict])
async def end_call(payload: CallEndPayload, db: AsyncSession = Depends(get_db)):
    logger.info(f"Calls API: Ending call {payload.vapi_call_id}")
    
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalar()
    org_id = org.id if org else 1
    
    # Broadcast update
    await broadcast_active_calls(org_id, db)
    
    # Correlate customer and dispatch EventBus alerts
    call_detail = await VapiService.get_call(payload.vapi_call_id)
    customer_phone = call_detail.get("customer", {}).get("number", "+15550199000") if call_detail else "+15550199000"
    
    cust_res = await db.execute(select(Customer).filter(Customer.phone == customer_phone))
    customer = cust_res.scalar()
    customer_id = customer.id if customer else 1
    
    # Dispatch event via EventBus (Background workers handle CRM / Google Calendar integrations)
    from app.events.event_types import CallEndedEvent
    from app.events.publisher import EventBus
    import uuid
    
    event = CallEndedEvent(
        event_id=str(uuid.uuid4()),
        vapi_call_id=payload.vapi_call_id,
        twilio_call_id=payload.twilio_call_id or (call_detail.get("phoneNumberId") if call_detail else None),
        duration=payload.duration,
        recording_url=payload.recording_url,
        summary=payload.summary,
        transcript=payload.transcript,
        cost=payload.cost,
        organization_id=org_id,
        customer_id=customer_id
    )
    await EventBus.publish(event)
    
    SessionManager.clear_session(payload.vapi_call_id)
    
    return StandardResponse(
        success=True,
        message="Call session successfully ended",
        data={}
    )

@router.post("/transcript", response_model=StandardResponse[dict])
async def update_transcript(payload: CallTranscriptPayload, db: AsyncSession = Depends(get_db)):
    logger.info(f"Calls API: Transcript update for {payload.vapi_call_id} ({payload.role}): {payload.text}")
    
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalar()
    org_id = org.id if org else 1
    
    # Update Session telemetry
    state = SessionManager.get_session(payload.vapi_call_id)
    state["last_utterance"] = payload.text
    
    if payload.role == "user":
        SessionManager.detect_intent(payload.vapi_call_id, payload.text)
        
        # Simulate dynamic confidence/latency updates during conversation
        import random
        state["llm_latency"] = round(random.uniform(0.6, 0.95), 2)
        state["search_latency"] = round(random.uniform(0.015, 0.045), 3)
        state["confidence_score"] = random.randint(93, 99)
        
    # Broadcast updated call details to dashboard WebSocket
    await broadcast_active_calls(org_id, db)
    
    # Broadcast live transcript line to the transcripts WebSocket
    from app.voice.websocket.websocket import manager as ws_manager
    await ws_manager.broadcast_transcript(payload.vapi_call_id, {
        "role": payload.role,
        "content": payload.text,
        "created_at": datetime.datetime.utcnow().isoformat()
    })
    
    return StandardResponse(
        success=True,
        message="Transcript updated successfully",
        data={}
    )

@router.post("/status", response_model=StandardResponse[dict])
async def update_call_status(payload: CallStatusPayload, db: AsyncSession = Depends(get_db)):
    logger.info(f"Calls API: Status update for {payload.vapi_call_id} to {payload.status}")
    
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalar()
    org_id = org.id if org else 1
    
    # Broadcast update
    await broadcast_active_calls(org_id, db)
    
    # Broadcast state transition alert
    from app.voice.websocket.websocket import manager as ws_manager
    await ws_manager.broadcast_call_event(org_id, {
        "call_id": get_int_id(payload.vapi_call_id),
        "vapi_call_id": payload.vapi_call_id,
        "status": payload.status,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    
    return StandardResponse(
        success=True,
        message="Call status updated successfully",
        data={}
    )

@router.get("", response_model=StandardResponse[list])
async def get_calls_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    logger.info(f"Calls API: Fetching Vapi call history for org {org_id}")
    
    vapi_calls = await VapiService.get_calls()
    
    calls_mapped = []
    for call in vapi_calls:
        cust_obj = call.get("customer") or {}
        customer_phone = cust_obj.get("number", "Unknown") if isinstance(cust_obj, dict) else "Unknown"
        if not customer_phone or customer_phone == "Unknown":
            customer_phone = "+15550199000"
        
        cust_res = await db.execute(select(Customer).filter(Customer.phone == customer_phone))
        cust = cust_res.scalar()
        if not cust:
            cust = Customer(
                name=f"Caller {customer_phone[-4:]}" if len(customer_phone) > 4 else "Caller",
                phone=customer_phone,
                organization_id=org_id
            )
            db.add(cust)
            await db.commit()
            await db.refresh(cust)
            
        analysis = call.get("analysis", {}) or {}
        created_at_str = call.get("createdAt", datetime.datetime.utcnow().isoformat())
        
        calls_mapped.append({
            "id": get_int_id(call.get("id")),
            "vapi_call_id": call.get("id"),
            "twilio_call_id": call.get("phoneNumberId"),
            "customer": {
                "id": cust.id,
                "name": cust.name,
                "phone": cust.phone,
                "email": cust.email
            },
            "status": call.get("status", "ended"),
            "duration": call.get("duration", 0),
            "summary": call.get("summary"),
            "sentiment": analysis.get("sentiment", "neutral"),
            "lead_score": analysis.get("leadScore", 0),
            "recording_url": call.get("recordingUrl"),
            "recordingUrl": call.get("recordingUrl"),
            "cost": call.get("cost", 0.0),
            "created_at": created_at_str,
            "type": call.get("type", "outboundPhoneCall"),
            "ended_reason": call.get("endedReason", "customer-ended-call"),
            "endedReason": call.get("endedReason", "customer-ended-call"),
            "analysis": analysis,
            "transcript": call.get("transcript", []),
            "messages": call.get("messages", [])
        })
    return StandardResponse(success=True, message="Call history sync successful", data=calls_mapped)

@router.get("/{call_id}/recording", response_model=StandardResponse[dict])
async def get_call_recording(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    logger.info(f"Calls API: Fetching recording metadata for id {call_id} for org {org_id}")

    vapi_call_id = call_id
    vapi_calls = await VapiService.get_calls()
    for call in vapi_calls:
        hashed_id = str(get_int_id(call.get("id")))
        if hashed_id == str(call_id) or str(call.get("id")) == str(call_id):
            vapi_call_id = call.get("id")
            break

    call_detail = await VapiService.get_call(vapi_call_id)
    if not call_detail:
        raise HTTPException(status_code=404, detail="Call record not found on Vapi")

    recording_url = call_detail.get("recordingUrl")
    return StandardResponse(
        success=True,
        message="Recording metadata fetched successfully",
        data={
            "available": bool(recording_url),
            "recordingUrl": recording_url,
            "expiresAt": call_detail.get("metadata", {}).get("expiresAt") or None,
            "provider": "Vapi",
            "status": call_detail.get("status")
        }
    )

@router.get("/{call_id}", response_model=StandardResponse[dict])
async def get_call_details(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    logger.info(f"Calls API: Fetching call details for id {call_id}")
    
    # Determine if call_id is a hashed integer
    vapi_call_id = call_id
    vapi_calls = await VapiService.get_calls()
    for call in vapi_calls:
        hashed_id = str(get_int_id(call["id"]))
        if hashed_id == str(call_id) or str(call["id"]) == str(call_id):
            vapi_call_id = call["id"]
            break
            
    # Fetch from Vapi Service
    call_detail = await VapiService.get_call(vapi_call_id)
    if not call_detail:
        raise HTTPException(status_code=404, detail="Call record not found on Vapi")
        
    cust_obj = call_detail.get("customer")
    customer_phone = cust_obj.get("number", "Unknown") if isinstance(cust_obj, dict) else "Unknown"
    if not customer_phone or customer_phone == "Unknown":
        customer_phone = "+15550199000"
    
    # Resolve customer
    cust_res = await db.execute(select(Customer).filter(Customer.phone == customer_phone))
    cust = cust_res.scalar()
    if not cust:
        cust = Customer(
            name=f"Caller {customer_phone[-4:]}" if len(customer_phone) > 4 else "Caller",
            phone=customer_phone,
            organization_id=org_id
        )
        db.add(cust)
        await db.commit()
        await db.refresh(cust)
        
    analysis = (call_detail.get("analysis") or {})
    raw_messages = call_detail.get("messages") or call_detail.get("transcript") or []
    messages_mapped = []
    for idx, msg in enumerate(raw_messages):
        if isinstance(msg, dict):
            role = msg.get("role") or msg.get("speaker") or "assistant"
            content = msg.get("message") or msg.get("content") or msg.get("text") or ""
            speaker = msg.get("speaker") or ("Customer" if str(role).lower() in {"user", "customer"} else "Assistant")
            if not content:
                continue
            messages_mapped.append({
                "id": idx + 1,
                "role": "user" if str(role).lower() in {"user", "customer"} else "assistant",
                "content": content,
                "speaker": speaker,
                "intent": msg.get("intent"),
                "created_at": msg.get("timestamp") or msg.get("time") or datetime.datetime.utcnow().isoformat()
            })
        elif isinstance(msg, str) and msg.strip():
            messages_mapped.append({
                "id": len(messages_mapped) + 1,
                "role": "assistant",
                "content": msg,
                "speaker": "Assistant",
                "intent": None,
                "created_at": datetime.datetime.utcnow().isoformat()
            })

    if not messages_mapped and isinstance(call_detail.get("transcriptText"), str) and call_detail.get("transcriptText"):
        messages_mapped.append({
            "id": 1,
            "role": "assistant",
            "content": call_detail.get("transcriptText"),
            "speaker": "Assistant",
            "intent": None,
            "created_at": datetime.datetime.utcnow().isoformat()
        })

    return StandardResponse(
        success=True,
        message="Call details fetched successfully",
        data={
            "id": get_int_id(call_detail.get("id")),
            "vapi_call_id": call_detail.get("id"),
            "twilio_call_id": call_detail.get("phoneNumberId"),
            "customer": {
                "id": cust.id,
                "name": cust.name,
                "phone": cust.phone,
                "email": cust.email
            },
            "status": call_detail.get("status", "ended"),
            "duration": call_detail.get("duration", 0),
            "summary": call_detail.get("summary"),
            "sentiment": analysis.get("sentiment", "neutral"),
            "lead_score": analysis.get("leadScore", 0),
            "recording_url": call_detail.get("recordingUrl"),
            "recordingUrl": call_detail.get("recordingUrl"),
            "cost": call_detail.get("cost", 0.0),
            "created_at": call_detail.get("createdAt", datetime.datetime.utcnow().isoformat()),
            "started_at": call_detail.get("startedAt"),
            "ended_at": call_detail.get("endedAt"),
            "ended_reason": call_detail.get("endedReason"),
            "endedReason": call_detail.get("endedReason"),
            "messages": messages_mapped,
            "transcript": messages_mapped,
            "transcriptText": call_detail.get("transcriptText"),
            "analysis": analysis,
            "artifacts": call_detail.get("artifacts", []),
            "provider": call_detail.get("provider"),
            "model": call_detail.get("model"),
            "voice": call_detail.get("voice"),
            "latencyMetrics": call_detail.get("latencyMetrics", {}),
            "toolCalls": call_detail.get("toolCalls", []),
            "metadata": call_detail.get("metadata", {})
        }
    )


@router.delete("/{call_id}", response_model=StandardResponse[dict])
async def delete_call(
    call_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from fastapi.responses import JSONResponse
    
    logger.info(f"Delete Flow: Call Endpoint Entered for call_id={call_id} by user={current_user.email}")
    try:
        org_id = current_user.organization_id
        
        # Check if the call exists in the database first
        # We search by local integer id or string vapi_call_id
        query = select(Call).filter(
            (Call.organization_id == org_id) & 
            ((Call.id == int(call_id) if call_id.isdigit() else False) | (Call.vapi_call_id == call_id))
        )
        result = await db.execute(query)
        call = result.scalar()
        
        if not call:
            # Let's search if the call belongs to another organization to return a 403 authorization error
            query_any = select(Call).filter(
                ((Call.id == int(call_id) if call_id.isdigit() else False) | (Call.vapi_call_id == call_id))
            )
            result_any = await db.execute(query_any)
            call_any = result_any.scalar()
            if call_any:
                logger.warning(f"Delete Flow: Permission Verification Failed for call_id={call_id} (Org mismatch: call={call_any.organization_id}, user={org_id})")
                return JSONResponse(
                    status_code=403,
                    content={
                        "success": False,
                        "stage": "Authentication",
                        "reason": "Call belongs to another organization"
                    }
                )
            
            logger.warning(f"Delete Flow: Call Record Not Located for call_id={call_id}")
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "stage": "Database",
                    "reason": "Call record not found"
                }
            )
            
        logger.info(f"Delete Flow: Call Record Located for call_id={call_id}")
        logger.info(f"Delete Flow: Call Permission Verified for call_id={call_id}")
        
        # Delete related messages manually to ensure constraint safety
        logger.info("Delete Flow: Call Related Records Deleting...")
        from app.models.models import Message
        messages_res = await db.execute(select(Message).filter(Message.call_id == call.id))
        messages = messages_res.scalars().all()
        for msg in messages:
            await db.delete(msg)
            
        vapi_call_id = call.vapi_call_id
        
        # Delete the call record itself
        await db.delete(call)
        await db.commit()
        logger.info("Delete Flow: Call Transaction Committed.")
        
        # Broadcast to dashboard to sync instantly
        await broadcast_active_calls(org_id, db)
        logger.info("Delete Flow: Call WebSocket refresh broadcasted.")
        
        logger.info("Delete Flow: Call Success Response Returned.")
        return StandardResponse(
            success=True,
            message="Call record successfully deleted from database",
            data={"deleted_id": call_id, "vapi_call_id": vapi_call_id}
        )
        
    except Exception as e:
        await db.rollback()
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Delete Flow failed at Database/Transaction stage in calls.py, delete_call:\n{tb}")
        return JSONResponse(
            status_code=550,
            content={
                "success": False,
                "stage": "Database",
                "reason": f"Database constraint or transactional error: {str(e)}"
            }
        )
