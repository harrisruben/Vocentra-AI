from fastapi import APIRouter, Depends, Form, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import Customer, Call, Organization
from app.core.logger import logger
import datetime

router = APIRouter(prefix="/webhooks/twilio", tags=["Webhooks"])

@router.post("", status_code=status.HTTP_200_OK)
async def twilio_inbound_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Twilio Webhook: CallSid={CallSid}, From={From}, To={To}, CallStatus={CallStatus}")
    
    # 1. Resolve organization (default sandbox org for local testing)
    org_result = await db.execute(select(Organization).limit(1))
    org = org_result.scalar()
    if not org:
        org = Organization(name="Default Sandbox Org")
        db.add(org)
        await db.commit()
        await db.refresh(org)
        logger.info(f"Initialized Default Sandbox Organization (id: {org.id})")
    
    # 2. Find or create Customer by phone
    cust_result = await db.execute(select(Customer).filter(Customer.phone == From))
    customer = cust_result.scalar()
    if not customer:
        customer = Customer(
            name=f"Caller {From[-4:]}",
            phone=From,
            organization_id=org.id
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        logger.info(f"Registered new customer profile: name='{customer.name}', phone='{From}' (id: {customer.id})")
        
    # 3. Create or update call details in database
    call_result = await db.execute(select(Call).filter(Call.twilio_call_id == CallSid))
    call = call_result.scalar()
    
    if not call:
        call = Call(
            twilio_call_id=CallSid,
            organization_id=org.id,
            customer_id=customer.id,
            status="ongoing",
            duration=0,
            cost=0.0
        )
        db.add(call)
        await db.commit()
        logger.info(f"Created new call log in database: twilio_call_id={CallSid} (id: {call.id})")
    else:
        call.status = CallStatus
        if CallStatus in ["completed", "failed", "busy", "no-answer"]:
            call.status = "completed" if CallStatus == "completed" else "failed"
        await db.commit()
        logger.info(f"Updated call status for twilio_call_id={CallSid} to {call.status}")
        
    # Broadcast updated active calls to frontend over WebSocket
    from app.voice.transcripts.transcripts import broadcast_active_calls
    await broadcast_active_calls(org.id, db)

    # Standard XML response for Twilio
    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Connecting to your Vocentra Voice Assistant.</Say>
</Response>"""
    return Response(content=twiml_response, media_type="application/xml")
