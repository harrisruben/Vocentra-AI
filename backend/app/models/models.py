import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.core.config import settings

# Dynamically set embedding type: use pgvector on Postgres, fallback to JSON on SQLite
if settings.DATABASE_URL.startswith("postgresql"):
    try:
        from pgvector.sqlalchemy import Vector
        embedding_type = Vector(1536)
    except ImportError:
        embedding_type = JSON
else:
    embedding_type = JSON


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # SaaS Billing & Quota Limits
    billing_tier = Column(String, default="free")  # free, growth, enterprise
    usage_limit = Column(Integer, default=100)      # max calls allowed per month
    usage_count = Column(Integer, default=0)        # current calls counted this month
    
    # Credentials & Third-Party Webhook configuration controls
    twilio_sid = Column(String, nullable=True)
    twilio_token = Column(String, nullable=True)
    vapi_assistant_id = Column(String, nullable=True)
    n8n_webhook_url = Column(String, nullable=True)
    working_hours = Column(JSON, nullable=True)     # e.g. {"mon": ["09:00", "17:00"]}
    call_delay = Column(Integer, default=30)        # Delay in seconds between sequential campaign calls
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="organization", cascade="all, delete-orphan")
    calls = relationship("Call", back_populates="organization", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="organization", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="organization", cascade="all, delete-orphan")
    knowledge_base = relationship("Knowledge", back_populates="organization", cascade="all, delete-orphan")
    campaigns = relationship("Campaign", back_populates="organization", cascade="all, delete-orphan")
    
    # Week 4 SaaS tables relations
    workflow_configs = relationship("WorkflowConfig", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="member")  # admin (owner), manager, member (agent)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Team invitation and session lifecycle tracking
    invite_token = Column(String, nullable=True)
    invite_expires = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="users")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, index=True, nullable=False)
    email = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="customers")
    calls = relationship("Call", back_populates="customer", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="customer", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="customer", cascade="all, delete-orphan")
    campaign_leads = relationship("CampaignLead", back_populates="customer")


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="draft")
    source_file_name = Column(String, nullable=True)
    source_file_type = Column(String, nullable=True)
    lead_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="campaigns")
    creator = relationship("User")
    leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")
    executions = relationship("CampaignExecution", back_populates="campaign", cascade="all, delete-orphan")


class CampaignLead(Base):
    __tablename__ = "campaign_leads"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    status = Column(String, default="queued")
    attempts = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    vapi_call_id = Column(String, nullable=True)
    
    # Executed call details
    assistant_id = Column(String, nullable=True)
    phone_number_id = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    duration = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    recording_url = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    ended_reason = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    campaign = relationship("Campaign", back_populates="leads")
    customer = relationship("Customer", back_populates="campaign_leads")


class CampaignExecution(Base):
    __tablename__ = "campaign_executions"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="queued")
    summary = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    campaign = relationship("Campaign", back_populates="executions")


class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    vapi_call_id = Column(String, unique=True, index=True, nullable=True)
    twilio_call_id = Column(String, index=True, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="completed")  # ongoing, completed, failed
    duration = Column(Integer, default=0)  # in seconds
    summary = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)  # positive, neutral, negative
    lead_score = Column(Integer, default=0)
    recording_url = Column(String, nullable=True)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="calls")
    customer = relationship("Customer", back_populates="calls")
    messages = relationship("Message", back_populates="call", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="call")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(Integer, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    intent = Column(String, nullable=True)  # pricing, scheduling, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    call = relationship("Call", back_populates="messages")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="new")  # new, contacted, qualified, lost, won
    lead_score = Column(Integer, default=0)
    value = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="leads")
    customer = relationship("Customer", back_populates="leads")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(Integer, ForeignKey("calls.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, default="AI Appointed Meeting")
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="appointments")
    customer = relationship("Customer", back_populates="appointments")
    call = relationship("Call", back_populates="appointments")


class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # pdf, webpage, text, faq
    text_content = Column(Text, nullable=False)
    embedding = Column(embedding_type, nullable=True)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="knowledge_base")


# --- Week 4 Commercial SaaS & Workflow Models ---

class WorkflowConfig(Base):
    __tablename__ = "workflow_configs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)            # e.g. "Twilio n8n Qualify Hub"
    webhook_url = Column(String, nullable=False)
    enabled = Column(Boolean, default=True)
    retries = Column(Integer, default=3)
    last_executed_at = Column(DateTime, nullable=True)
    last_status = Column(String, nullable=True)      # success, failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="workflow_configs")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)            # e.g. "Dev HubSpot Key"
    key_prefix = Column(String, nullable=False)      # e.g. "sk_live_a12b"
    hashed_key = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    organization = relationship("Organization", back_populates="api_keys")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)          # user_invited, settings_modified, api_key_rotated
    description = Column(Text, nullable=False)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="audit_logs")
    user = relationship("User")
