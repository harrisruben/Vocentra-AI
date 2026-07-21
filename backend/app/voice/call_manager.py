import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Call, Customer
from app.core.logger import logger
from app.events.publisher import EventBus
from app.events.event_types import CallEndedEvent

class CallManager:
    @staticmethod
    async def finalize_call(
        vapi_call_id: str,
        twilio_call_id: str,
        duration: int,
        recording_url: str,
        summary: str,
        transcript: str,
        cost: float,
        db: AsyncSession
    ) -> None:
        logger.info(f"CallManager: Finalizing call logs for twilio_sid='{twilio_call_id}', vapi_id='{vapi_call_id}'")
        
        # Load the Call record
        query = select(Call).filter(
            (Call.vapi_call_id == vapi_call_id) | (Call.twilio_call_id == twilio_call_id)
        )
        result = await db.execute(query)
        call = result.scalar()
        
        if not call:
            logger.warning("No pre-registered call record found. Logging fallback Call record.")
            # Sandbox fallback: bind call to first customer
            cust_res = await db.execute(select(Customer).limit(1))
            customer = cust_res.scalar()
            if not customer:
                logger.error("Cannot finalize call. No default Customer exists in SQLite.")
                return
            call = Call(
                twilio_call_id=twilio_call_id,
                organization_id=customer.organization_id,
                customer_id=customer.id
            )
            db.add(call)
            await db.flush()
            
        # Update metrics
        call.vapi_call_id = vapi_call_id
        if twilio_call_id:
            call.twilio_call_id = twilio_call_id
        call.status = "completed"
        call.duration = duration
        call.recording_url = recording_url
        call.summary = summary
        call.cost = cost
        
        # Calculate mock sentiment/lead scores based on transcript keywords
        call.sentiment = "neutral"
        if transcript:
            text = transcript.lower()
            if any(w in text for w in ["great", "thank", "good", "perfect", "yes", "super", "awesome"]):
                call.sentiment = "positive"
                call.lead_score = 90
            elif any(w in text for w in ["bad", "issue", "no", "error", "fail", "broken", "stop"]):
                call.sentiment = "negative"
                call.lead_score = 30
            else:
                call.lead_score = 65
                
        await db.commit()
        logger.info(f"Call finalized in DB: call_id={call.id}, duration={duration}s, cost=${cost:.3f}")
        
        # Publish CallEndedEvent for background subscribers (CRM sync, emails, Slack alerts)
        event = CallEndedEvent(
            event_id=str(uuid.uuid4()),
            twilio_call_id=twilio_call_id,
            vapi_call_id=vapi_call_id,
            duration=duration,
            recording_url=recording_url,
            summary=summary,
            transcript=transcript,
            cost=cost,
            organization_id=call.organization_id,
            customer_id=call.customer_id
        )
        await EventBus.publish(event)
        logger.info(f"CallEndedEvent published for call_id={call.id}")
        
        return
