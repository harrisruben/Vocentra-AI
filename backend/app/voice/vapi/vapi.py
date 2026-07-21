from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.logger import logger
from app.ai.orchestrator.ai_orchestrator import AIOrchestrator
from app.voice.call_manager import CallManager
from app.voice.session_manager import SessionManager
from app.voice.transcripts.transcripts import broadcast_active_calls
from app.models.models import Call, Customer, Organization
from typing import Optional, Dict, Any

router = APIRouter(prefix="/webhooks/vapi", tags=["Webhooks"])

async def get_or_create_call(
    vapi_call_id: str,
    twilio_call_id: str,
    customer_phone: str,
    db: AsyncSession,
    metadata: Optional[dict] = None
) -> Call:
    # 1. Check if call already exists
    query = select(Call).filter(
        (Call.vapi_call_id == vapi_call_id) | 
        (Call.twilio_call_id == twilio_call_id) if twilio_call_id else False
    )
    result = await db.execute(query)
    call = result.scalar()
    if call:
        # Update vapi_call_id if it was created by Twilio without it
        if not call.vapi_call_id and vapi_call_id:
            call.vapi_call_id = vapi_call_id
            await db.commit()
        return call
        
    # 2. Resolve organization from metadata, else default Sandbox Org
    org_id = metadata.get("org_id") if metadata else None
    org = None
    if org_id:
        org_res = await db.execute(select(Organization).filter(Organization.id == org_id))
        org = org_res.scalar()
        
    if not org:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar()
        
    if not org:
        org = Organization(name="Default Sandbox Org")
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
    # 3. Resolve customer from metadata, else by phone
    customer = None
    customer_id = metadata.get("customer_id") if metadata else None
    if customer_id:
        cust_res = await db.execute(select(Customer).filter(Customer.id == customer_id))
        customer = cust_res.scalar()
        
    if not customer and customer_phone:
        cust_res = await db.execute(select(Customer).filter(Customer.phone == customer_phone, Customer.organization_id == org.id))
        customer = cust_res.scalar()
        
    if not customer:
        customer = Customer(
            name=f"Caller {customer_phone[-4:]}" if customer_phone else "Unknown Caller",
            phone=customer_phone or "+15555555555",
            organization_id=org.id
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)
        
    call = Call(
        vapi_call_id=vapi_call_id,
        twilio_call_id=twilio_call_id,
        organization_id=org.id,
        customer_id=customer.id,
        status="ongoing",
        duration=0,
        cost=0.0
    )
    db.add(call)
    await db.commit()
    await db.refresh(call)
    logger.info(f"Vapi Webhook: Created new Call record vapi_call_id={vapi_call_id} for org={org.id}")
    return call

@router.post("")
async def vapi_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.json()
    message = payload.get("message", {})
    message_type = message.get("type")
    
    logger.info(f"Vapi Webhook Trigger: event_type='{message_type}'")
    
    # 1. Dynamic Assistant setup trigger
    if message_type == "assistant-request":
        call_details = payload.get("call", {})
        vapi_call_id = call_details.get("id")
        twilio_call_id = call_details.get("twilioCallSid")
        customer_phone = call_details.get("customer", {}).get("number")
        
        # Load compiled dynamic config
        assistant_config = await AIOrchestrator.get_dynamic_assistant(customer_phone, db)
        
        # Resolve call log to keep db consistent
        metadata = call_details.get("metadata", {}) or {}
        call = await get_or_create_call(vapi_call_id, twilio_call_id, customer_phone, db, metadata)
        await broadcast_active_calls(call.organization_id, db)
        
        return JSONResponse(status_code=200, content={"assistant": assistant_config})
        
    # 2. Vapi tool calling execution pipeline
    elif message_type == "tool-calls":
        tool_calls_list = message.get("toolCalls", [])
        tool_results = []
        
        call_details = payload.get("call", {})
        vapi_call_id = call_details.get("id")
        twilio_call_id = call_details.get("twilioCallSid")
        customer_phone = call_details.get("customer", {}).get("number")
        session_id = vapi_call_id or twilio_call_id or "MOCK"
        
        metadata = call_details.get("metadata", {}) or {}
        call = await get_or_create_call(vapi_call_id, twilio_call_id, customer_phone, db, metadata)
        
        for tool_call in tool_calls_list:
            tool_id = tool_call.get("id")
            function_name = tool_call.get("function", {}).get("name")
            arguments = tool_call.get("function", {}).get("arguments", {})
            
            logger.info(f"Vapi Webhook: Running tool function '{function_name}' with args: {arguments}")
            result = await AIOrchestrator.execute_tool(function_name, arguments, db)
            
            if function_name == "book_appointment" and result.get("success"):
                SessionManager.save_slot(session_id, "date_str", arguments.get("datetime_str", "").split(" ")[0])
                SessionManager.save_slot(session_id, "title", arguments.get("title", ""))
            elif function_name == "create_crm_lead" and result.get("success"):
                SessionManager.save_slot(session_id, "lead_created", "true")
            
            tool_results.append({
                "toolCallId": tool_id,
                "result": result
            })
            
        # Update transient session telemetry
        state = SessionManager.get_session(session_id)
        state["last_utterance"] = f"Executed tool: {', '.join([tc.get('function', {}).get('name') for tc in tool_calls_list])}"
        state["tool_latency"] = 0.180
        
        await broadcast_active_calls(call.organization_id, db)
        return JSONResponse(status_code=200, content={"results": tool_results})
        
    # 3. Post-call analytics and database finalization
    elif message_type == "end-of-call-report":
        call_details = payload.get("call", {})
        vapi_call_id = call_details.get("id")
        twilio_call_id = call_details.get("twilioCallSid")
        duration = payload.get("duration") or call_details.get("duration") or 0
        recording_url = payload.get("recordingUrl") or call_details.get("recordingUrl")
        summary = payload.get("summary")
        transcript = payload.get("transcript")
        cost = payload.get("cost") or 0.0
        
        await CallManager.finalize_call(
            vapi_call_id=vapi_call_id,
            twilio_call_id=twilio_call_id,
            duration=duration,
            recording_url=recording_url,
            summary=summary,
            transcript=transcript,
            cost=cost,
            db=db
        )
        
        # Check if call is linked to a CampaignLead
        from app.models.models import Campaign, CampaignLead
        from app.workers.campaign_worker import broadcast_campaign_progress
        import datetime
        
        lead_res = await db.execute(select(CampaignLead).filter(CampaignLead.vapi_call_id == vapi_call_id))
        lead = lead_res.scalar()
        if lead:
            lead.status = "completed" if (call_details.get("status") or "").lower() in ["ended", "completed"] else "failed"
            lead.ended_at = datetime.datetime.utcnow()
            lead.duration = duration
            lead.cost = cost
            lead.recording_url = recording_url
            lead.summary = summary
            lead.transcript = transcript
            lead.ended_reason = call_details.get("endedReason", "customer-ended-call")
            
            campaign = await db.get(Campaign, lead.campaign_id)
            if campaign:
                if lead.status == "completed":
                    campaign.completed_count = min(campaign.lead_count, campaign.completed_count + 1)
                else:
                    campaign.failed_count = min(campaign.lead_count, campaign.failed_count + 1)
                
                await db.commit()
                await broadcast_campaign_progress(campaign.id, db)

        # Broadcast completed state to update UI
        query = select(Call).filter(
            (Call.vapi_call_id == vapi_call_id) | (Call.twilio_call_id == twilio_call_id)
        )
        call_res = await db.execute(query)
        call = call_res.scalar()
        if call:
            await broadcast_active_calls(call.organization_id, db)
            
        session_id = vapi_call_id or twilio_call_id or "MOCK"
        SessionManager.clear_session(session_id)
        
        return JSONResponse(status_code=200, content={"success": True})
        
    # 4. Real-time transcript streaming
    elif message_type in ["transcript", "speech-update", "conversation-update"]:
        call_details = payload.get("call", {})
        vapi_call_id = call_details.get("id")
        twilio_call_id = call_details.get("twilioCallSid")
        customer_phone = call_details.get("customer", {}).get("number")
        session_id = vapi_call_id or twilio_call_id or "MOCK"
        
        metadata = call_details.get("metadata", {}) or {}
        call = await get_or_create_call(vapi_call_id, twilio_call_id, customer_phone, db, metadata)
        
        transcript_text = message.get("transcript", "") or message.get("text", "")
        if transcript_text:
            state = SessionManager.get_session(session_id)
            state["last_utterance"] = transcript_text
            
            # Run intent detector
            SessionManager.detect_intent(session_id, transcript_text)
            
            # Simulated real-time latency dashboard indicators
            import random
            state["llm_latency"] = round(random.uniform(0.6, 0.95), 2)
            state["search_latency"] = round(random.uniform(0.015, 0.045), 3)
            state["confidence_score"] = random.randint(93, 99)
            
            await broadcast_active_calls(call.organization_id, db)
            
    return JSONResponse(status_code=200, content={"success": True})
