from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.memory.long_term import LongTermMemory
from app.core.logger import logger

class ProfileEngine:
    """Compiles short-term and long-term customer logs into dynamic prompt profile context snippets."""
    
    @staticmethod
    async def compile_memory_profile(phone: str, db: AsyncSession) -> str:
        history = await LongTermMemory.get_customer_history(phone, db)
        if not history or not history.get("exists"):
            return "This is a new customer. Greet them warmly and ask how we can help."
            
        customer = history["customer"]
        total_calls = history["total_calls"]
        last_call = history["last_call"]
        appts = history["appointments"]
        
        profile_parts = [
            f"Caller Profile: Customer Name is '{customer.name}'. Phone is '{customer.phone}'.",
            f"Interaction Count: This customer has made {total_calls} calls previously."
        ]
        
        # Merge last call summary details
        if last_call:
            profile_parts.append(
                f"Last call occurred on {last_call.created_at.strftime('%Y-%m-%d')}. "
                f"Previous call summary: '{last_call.summary or 'No summary logged'}'."
                f"Previous call sentiment was: {last_call.sentiment}."
            )
            
        # Merge upcoming appointment details
        scheduled_appts = [a for a in appts if a.status == "scheduled"]
        if scheduled_appts:
            next_appt = scheduled_appts[0]
            profile_parts.append(
                f"Active Appointment: Scheduled for {next_appt.start_time.strftime('%Y-%m-%d %I:%M %p')} "
                f"titled '{next_appt.title}'."
            )
            
        compiled_profile = " ".join(profile_parts)
        logger.info(f"ProfileEngine: Compiled caller context: '{compiled_profile[:90]}...'")
        return compiled_profile
