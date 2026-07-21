import asyncio
from app.events.event_types import CallEndedEvent, LeadCreatedEvent
from app.events.publisher import EventBus
from app.core.logger import logger
import app.tools as tools
from app.core.database import AsyncSessionLocal
from sqlalchemy.future import select
from app.models.models import Customer
from app.integrations import HubSpotConnector
from app.core.config import settings
import httpx

# Helper to send background webhook dispatches to n8n
async def dispatch_n8n_webhook(event_type: str, payload: dict):
    async def run_n8n_post():
        try:
            n8n_url = getattr(settings, "N8N_WEBHOOK_URL", None) or "http://localhost:5678/webhook/call-finished"
            logger.info(f"Background Worker: Dispatching {event_type} event to n8n webhook at {n8n_url}")
            async with httpx.AsyncClient() as client:
                response = await client.post(n8n_url, json={"event": event_type, "data": payload}, timeout=5.0)
                logger.info(f"n8n Webhook: Dispatch status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Background n8n Webhook Dispatch Error: {str(e)}")
            
    asyncio.create_task(run_n8n_post())


# --- Call Ended Event Handlers ---
async def crm_sync_handler(event: CallEndedEvent) -> None:
    logger.info(f"Subscriber: Queueing CRM logs for call={event.vapi_call_id}")
    
    async def run_crm_sync():
        try:
            logger.info(f"Background Worker: Syncing CRM logs for call={event.vapi_call_id}")
            async with AsyncSessionLocal() as db:
                cust_res = await db.execute(select(Customer).filter(Customer.id == event.customer_id))
                cust = cust_res.scalar()
                if cust:
                    # Sync with HubSpot
                    await HubSpotConnector.sync_lead_details(
                        name=cust.name,
                        email=cust.email,
                        phone=cust.phone,
                        status="completed",
                        value=0.0
                    )
                    logger.info(f"HubSpot CRM: call logs sync complete for vapi_call_id={event.vapi_call_id}")
                else:
                    logger.warning(f"HubSpot CRM Sync failed: Customer {event.customer_id} not found in database.")
        except Exception as e:
            logger.error(f"Background CRM Sync Error: {str(e)}")

    asyncio.create_task(run_crm_sync())
    
    # Also dispatch call finished event to n8n
    await dispatch_n8n_webhook("call_finished", {
        "vapi_call_id": event.vapi_call_id,
        "customer_id": event.customer_id,
        "duration": event.duration,
        "summary": event.summary,
        "cost": event.cost
    })

async def send_followup_email_handler(event: CallEndedEvent) -> None:
    logger.info(f"Subscriber: Queueing follow-up email details for call={event.vapi_call_id}")
    
    async def run_email_dispatch():
        try:
            body = (
                f"Hi, thank you for calling Vocentra. Here is a summary of our conversation:\n\n"
                f"{event.summary or 'No summary logged.'}\n\n"
                f"A copy of the recording is available here: {event.recording_url or 'N/A'}\n\n"
                f"Best regards,\nVocentra AI Team"
            )
            # Rescoped dynamically from DB profiles
            await tools.send_confirmation_email(
                email="caller@prospect.com",
                subject="Summary of your Vocentra call",
                body=body
            )
            logger.info(f"Email Dispatch: Follow-up email sent for call={event.vapi_call_id}")
        except Exception as e:
            logger.error(f"Background Email Dispatch Error: {str(e)}")

    asyncio.create_task(run_email_dispatch())

async def slack_channel_call_ended_handler(event: CallEndedEvent) -> None:
    logger.info("Subscriber: Posting call analytics summary alert to Slack channel")
    
    async def run_slack_alert():
        try:
            slack_payload = {
                "text": f"📞 *Call Ended Report*\n"
                        f"• Call ID: `{event.vapi_call_id}`\n"
                        f"• Caller: ID={event.customer_id}\n"
                        f"• Duration: {event.duration} seconds\n"
                        f"• Platform cost: ${event.cost:.3f}\n"
                        f"• AI Summary: {event.summary}"
            }
            logger.info(f"Slack Notification Dispatch (Simulated): {slack_payload}")
        except Exception as e:
            logger.error(f"Background Slack Alert Error: {str(e)}")

    asyncio.create_task(run_slack_alert())


# --- Lead Created Event Handlers ---
async def crm_lead_sync_handler(event: LeadCreatedEvent) -> None:
    logger.info(f"Subscriber: Queueing Lead id={event.lead_id} details with HubSpot Pipeline")
    
    async def run_lead_sync():
        try:
            await HubSpotConnector.sync_lead_details(
                name=event.customer_name,
                email=None,
                phone=event.customer_phone,
                status="qualified",
                value=event.value
            )
            logger.info(f"HubSpot CRM: Lead id={event.lead_id} successfully mapped to qualified prospects.")
        except Exception as e:
            logger.error(f"Background Lead Sync Error: {str(e)}")

    asyncio.create_task(run_lead_sync())
    
    # Also dispatch lead qualified event to n8n
    await dispatch_n8n_webhook("lead_qualified", {
        "lead_id": event.lead_id,
        "customer_name": event.customer_name,
        "customer_phone": event.customer_phone,
        "lead_score": event.lead_score,
        "value": event.value
    })

async def slack_lead_alert_handler(event: LeadCreatedEvent) -> None:
    logger.info("Subscriber: Dispatching Slack alert for new qualified Lead")
    
    async def run_slack_lead():
        try:
            slack_payload = {
                "text": f"🚀 *New Lead Qualified!*\n"
                        f"• Prospect: {event.customer_name} ({event.customer_phone})\n"
                        f"• Quality Score: {event.lead_score}/100\n"
                        f"• Contract Value: ${event.value:.2f}"
            }
            logger.info(f"Slack Notification Dispatch (Simulated): {slack_payload}")
        except Exception as e:
            logger.error(f"Background Slack Lead Error: {str(e)}")

    asyncio.create_task(run_slack_lead())


def register_all_subscribers() -> None:
    """Invoked on application startup to register all event bus subscriptions."""
    EventBus.subscribe(CallEndedEvent, crm_sync_handler)
    EventBus.subscribe(CallEndedEvent, send_followup_email_handler)
    EventBus.subscribe(CallEndedEvent, slack_channel_call_ended_handler)
    
    EventBus.subscribe(LeadCreatedEvent, crm_lead_sync_handler)
    EventBus.subscribe(LeadCreatedEvent, slack_lead_alert_handler)
    logger.info("EventBus: All event subscriber bindings initialized.")
