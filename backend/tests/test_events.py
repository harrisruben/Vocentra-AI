from unittest.mock import AsyncMock, patch
import pytest
import uuid
from app.events.event_types import CallEndedEvent
from app.events.publisher import EventBus
import app.events.subscriber as sub

@pytest.mark.asyncio
async def test_event_bus_dispatch() -> None:
    """Verifies that publishing events dispatches async mock handlers correctly."""
    # Clear any active event subscribers to ensure clean registration
    EventBus._subscribers.clear()
    
    # 1. Patch the subscriber handler references before registering
    with patch("app.events.subscriber.crm_sync_handler", new_callable=AsyncMock) as mock_crm, \
         patch("app.events.subscriber.send_followup_email_handler", new_callable=AsyncMock) as mock_email, \
         patch("app.events.subscriber.slack_channel_call_ended_handler", new_callable=AsyncMock) as mock_slack:
         
        # Bind the mock handlers to the Event Bus
        sub.register_all_subscribers()
        
        # 2. Publish CallEndedEvent
        event = CallEndedEvent(
            event_id=str(uuid.uuid4()),
            twilio_call_id="twilio_test_sid_99",
            vapi_call_id="vapi_test_id_99",
            duration=180,
            recording_url="https://mock-s3.amazonaws.com/voice.wav",
            summary="Caller wanted a product demonstration.",
            transcript="Hello, I want to book a product demo for tomorrow afternoon.",
            cost=0.54,
            organization_id=1,
            customer_id=5
        )
        
        await EventBus.publish(event)
        
        # 3. Assert mock handlers were invoked with the event payload
        mock_crm.assert_called_once_with(event)
        mock_email.assert_called_once_with(event)
        mock_slack.assert_called_once_with(event)
