import datetime
from pydantic import BaseModel
from typing import Optional

class VocentraEvent(BaseModel):
    event_id: str
    timestamp: datetime.datetime = datetime.datetime.utcnow()

class CallEndedEvent(VocentraEvent):
    twilio_call_id: Optional[str]
    vapi_call_id: str
    duration: int
    recording_url: Optional[str]
    summary: Optional[str]
    transcript: Optional[str]
    cost: float
    organization_id: int
    customer_id: int

class LeadCreatedEvent(VocentraEvent):
    lead_id: int
    organization_id: int
    customer_name: str
    customer_phone: str
    lead_score: int
    value: float
