import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Customer, Lead
from app.core.logger import logger
from app.events.publisher import EventBus
from app.events.event_types import LeadCreatedEvent
from app.tools.registry import ToolRegistry

@ToolRegistry.register(
    name="create_crm_lead",
    description="Logs a new qualified lead in HubSpot CRM.",
    parameters={
        "type": "object",
        "properties": {
            "organization_id": {"type": "integer"},
            "name": {"type": "string"},
            "phone": {"type": "string"},
            "email": {"type": "string"},
            "notes": {"type": "string"}
        },
        "required": ["organization_id", "name", "phone"]
    },
    required_permissions=["agent"]
)
async def create_crm_lead(
    organization_id: int,
    name: str,
    phone: str,
    email: str,
    notes: str,
    db: AsyncSession
) -> dict:
    logger.info(f"Tool Run: create_crm_lead for {name} ({phone})")
    
    # Retrieve or create customer profile
    cust_res = await db.execute(select(Customer).filter(Customer.phone == phone))
    customer = cust_res.scalar()
    if not customer:
        customer = Customer(
            name=name,
            phone=phone,
            email=email,
            organization_id=organization_id
        )
        db.add(customer)
        await db.flush()
    else:
        if email and not customer.email:
            customer.email = email
            await db.flush()
            
    # Create Lead
    lead = Lead(
        organization_id=organization_id,
        customer_id=customer.id,
        status="qualified",
        lead_score=85,
        value=1200.00,
        notes=notes
    )
    db.add(lead)
    await db.commit()
    
    # Publish LeadCreatedEvent to the Event Bus for background subscribers
    event = LeadCreatedEvent(
        event_id=str(uuid.uuid4()),
        lead_id=lead.id,
        organization_id=organization_id,
        customer_name=customer.name,
        customer_phone=customer.phone,
        lead_score=lead.lead_score,
        value=lead.value
    )
    await EventBus.publish(event)
    
    logger.info(f"CRM Sync: Lead {lead.id} created and LeadCreatedEvent published.")
    return {
        "success": True,
        "lead_id": lead.id,
        "message": f"Lead recorded in HubSpot. Status: qualified, Score: {lead.lead_score}"
    }
