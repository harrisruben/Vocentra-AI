import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Customer, Organization
from app.ai.orchestrator.conversation_manager import ConversationManager
from app.analytics.analytics_service import AnalyticsService
from app.core.logger import logger
import app.tools as tools

class AIOrchestrator:
    @staticmethod
    async def get_dynamic_assistant(customer_phone: str, db: AsyncSession) -> dict:
        logger.info(f"AIOrchestrator: Assembling dynamic configuration for caller={customer_phone}")
        
        # Resolve caller profile
        org_result = await db.execute(select(Organization).limit(1))
        org = org_result.scalar()
        org_id = org.id if org else 1
        
        cust_result = await db.execute(select(Customer).filter(Customer.phone == customer_phone))
        customer = cust_result.scalar()
        customer_name = customer.name if customer else "valued caller"
        
        # Compile system prompts dynamically
        system_prompt = ConversationManager.compile_prompt("general")
        system_prompt = system_prompt.replace("Warmly", f"Warmly address them as {customer_name}")
        
        # Expose custom tool schemas for Vapi tool-calling
        vapi_tools = [
            {
                "type": "function",
                "name": "check_calendar_slots",
                "description": "Inspect open time slots on a specific date in YYYY-MM-DD format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date_str": {"type": "string", "description": "The target date (e.g. 2026-07-15)"}
                    },
                    "required": ["date_str"]
                }
            },
            {
                "type": "function",
                "name": "book_appointment",
                "description": "Schedule a meeting slot for this user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "datetime_str": {"type": "string", "description": "Proposed date and time (format YYYY-MM-DD HH:MM)"},
                        "title": {"type": "string", "description": "Description of the session"}
                    },
                    "required": ["datetime_str"]
                }
            },
            {
                "type": "function",
                "name": "create_crm_lead",
                "description": "Register caller contact info as a sales lead in the CRM pipeline.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Caller full name"},
                        "email": {"type": "string", "description": "Business email address"},
                        "notes": {"type": "string", "description": "Lead requirements details"}
                    },
                    "required": ["name", "email"]
                }
            }
        ]
        
        first_message = f"Hello {customer_name}, thank you for calling Vocentra. How can I help you today?"
        
        return {
            "name": "Vocentra AI Inbound Assistant",
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ]
            },
            "firstMessage": first_message,
            "tools": vapi_tools
        }

    @staticmethod
    async def execute_tool(function_name: str, arguments: dict, db: AsyncSession) -> dict:
        start_time = time.time()
        logger.info(f"AIOrchestrator: Routing function execution trigger: '{function_name}'")
        
        # Load default organization
        org_result = await db.execute(select(Organization).limit(1))
        org = org_result.scalar()
        org_id = org.id if org else 1
        
        # Resolve phone
        customer_phone = arguments.get("phone")
        if not customer_phone:
            # Fallback to first available phone
            cust_res = await db.execute(select(Customer).limit(1))
            customer = cust_res.scalar()
            customer_phone = customer.phone if customer else "+15555555555"
            customer_name = customer.name if customer else "Valued Caller"
        else:
            cust_res = await db.execute(select(Customer).filter(Customer.phone == customer_phone))
            customer = cust_res.scalar()
            customer_name = customer.name if customer else "Valued Caller"

        result = {"success": False, "message": "Tool function mapping not found."}
        
        try:
            if function_name == "check_calendar_slots":
                result = await tools.check_calendar_slots(
                    date_str=arguments.get("date_str")
                )
            elif function_name == "book_appointment":
                result = await tools.book_appointment(
                    organization_id=org_id,
                    phone=customer_phone,
                    name=customer_name,
                    datetime_str=arguments.get("datetime_str"),
                    title=arguments.get("title", "Discovery Session"),
                    db=db
                )
            elif function_name == "create_crm_lead":
                result = await tools.create_crm_lead(
                    organization_id=org_id,
                    name=arguments.get("name"),
                    phone=customer_phone,
                    email=arguments.get("email"),
                    notes=arguments.get("notes", "Lead captured from voice assistant call."),
                    db=db
                )
            elif function_name == "send_confirmation_email":
                result = await tools.send_confirmation_email(
                    email=arguments.get("email"),
                    subject=arguments.get("subject"),
                    body=arguments.get("body")
                )
        except Exception as e:
            logger.error(f"Failed to execute tool {function_name}: {str(e)}")
            result = {"success": False, "message": f"Execution error: {str(e)}"}
            
        execution_duration = time.time() - start_time
        
        # Log to observability service
        AnalyticsService.record_metrics(
            call_sid="VAPI-SESSION-TOOL",
            latency=execution_duration,
            tokens_used=15,
            tool_execution_time=execution_duration,
            errors_count=0 if result.get("success") else 1
        )
        
        return result
