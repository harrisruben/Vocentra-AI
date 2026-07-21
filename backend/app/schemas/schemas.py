from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# --- Campaign Schemas ---
class CampaignLeadBase(BaseModel):
    name: Optional[str] = None
    phone: str
    email: Optional[EmailStr] = None

class CampaignLeadResponse(CampaignLeadBase):
    id: int
    campaign_id: int
    customer_id: Optional[int] = None
    status: str
    attempts: int
    last_error: Optional[str] = None
    vapi_call_id: Optional[str] = None
    assistant_id: Optional[str] = None
    phone_number_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration: int
    cost: float
    recording_url: Optional[str] = None
    summary: Optional[str] = None
    transcript: Optional[str] = None
    ended_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None

class CampaignCreate(CampaignBase):
    pass

class CampaignResponse(CampaignBase):
    id: int
    organization_id: int
    created_by_user_id: Optional[int] = None
    status: str
    source_file_name: Optional[str] = None
    source_file_type: Optional[str] = None
    lead_count: int
    completed_count: int
    failed_count: int
    payload: Optional[dict] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CampaignProgressResponse(BaseModel):
    campaign: CampaignResponse
    leads: List[CampaignLeadResponse]

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None
    organization_id: Optional[int] = None

# --- Organization Schemas ---
class OrganizationBase(BaseModel):
    name: str

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    organization_name: str  # Users create a new organization on signup
    role: Optional[str] = "admin"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Customer Schemas ---
class CustomerBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    organization_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Call Schemas ---
class CallBase(BaseModel):
    vapi_call_id: Optional[str] = None
    twilio_call_id: Optional[str] = None
    customer_id: int
    status: str
    duration: int
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    lead_score: int
    recording_url: Optional[str] = None
    cost: float

class CallCreate(CallBase):
    pass

class CallResponse(BaseModel):
    id: int
    vapi_call_id: Optional[str] = None
    twilio_call_id: Optional[str] = None
    customer: CustomerResponse
    status: str
    duration: int
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    lead_score: int
    recording_url: Optional[str] = None
    cost: float
    created_at: datetime
    type: Optional[str] = None
    ended_reason: Optional[str] = None

    class Config:
        from_attributes = True

# --- Message Schemas ---
class MessageBase(BaseModel):
    role: str
    content: str
    intent: Optional[str] = None

class MessageResponse(MessageBase):
    id: int
    call_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Lead Schemas ---
class LeadBase(BaseModel):
    customer_id: int
    status: str
    lead_score: int
    value: float
    notes: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadResponse(BaseModel):
    id: int
    customer: CustomerResponse
    status: str
    lead_score: int
    value: float
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Appointment Schemas ---
class AppointmentBase(BaseModel):
    customer_id: int
    call_id: Optional[int] = None
    title: str
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentResponse(BaseModel):
    id: int
    customer: CustomerResponse
    call_id: Optional[int] = None
    title: str
    start_time: datetime
    end_time: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Dashboard Widget Schemas ---
class DashboardWidget(BaseModel):
    title: str
    value: str
    change: str
    type: str  # positive, negative, neutral

class DashboardResponse(BaseModel):
    today_calls: DashboardWidget
    active_calls: DashboardWidget
    missed_calls: DashboardWidget
    appointments: DashboardWidget
    revenue: DashboardWidget
    lead_score: DashboardWidget
    call_duration: DashboardWidget
    customer_satisfaction: DashboardWidget
    recent_calls: List[CallResponse]
    upcoming_appointments: List[AppointmentResponse]

# --- Analytics Response ---
class ChartDataPoint(BaseModel):
    label: str
    value: float

class AnalyticsResponse(BaseModel):
    calls_over_time: List[ChartDataPoint]
    satisfaction_distribution: List[ChartDataPoint]
    conversion_rates: List[ChartDataPoint]


# --- Standard Response Envelope ---
from typing import TypeVar, Generic

T = TypeVar("T")

class StandardResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Request processed successfully"
    data: Optional[T] = None

