from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Customer, Call, Appointment, Lead
from app.core.logger import logger

class LongTermMemory:
    """Retrieves long-term historical records for customers from the database."""
    
    @staticmethod
    async def get_customer_history(phone: str, db: AsyncSession) -> dict:
        logger.info(f"LongTermMemory: Fetching context records for phone: '{phone}'")
        
        # 1. Fetch customer details
        cust_query = select(Customer).filter(Customer.phone == phone)
        result = await db.execute(cust_query)
        customer = result.scalar()
        if not customer:
            logger.info(f"LongTermMemory: Customer record not found for phone '{phone}'")
            return {"exists": False}
            
        # 2. Fetch past calls
        calls_query = (
            select(Call)
            .filter(Call.customer_id == customer.id)
            .order_by(Call.created_at.desc())
        )
        calls_result = await db.execute(calls_query)
        calls = list(calls_result.scalars().all())
        
        # 3. Fetch appointments
        appts_query = (
            select(Appointment)
            .filter(Appointment.customer_id == customer.id)
            .order_by(Appointment.start_time.desc())
        )
        appts_result = await db.execute(appts_query)
        appts = list(appts_result.scalars().all())
        
        # 4. Fetch leads
        leads_query = select(Lead).filter(Lead.customer_id == customer.id)
        leads_result = await db.execute(leads_query)
        leads = list(leads_result.scalars().all())
        
        return {
            "exists": True,
            "customer": customer,
            "total_calls": len(calls),
            "calls": calls,
            "last_call": calls[0] if calls else None,
            "appointments": appts,
            "leads": leads
        }
