import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.models import Message
from app.core.logger import logger

class ConversationManager:
    @staticmethod
    async def get_history(call_id: int, db: AsyncSession) -> list:
        # Load all structured message histories for this session
        result = await db.execute(
            select(Message)
            .filter(Message.call_id == call_id)
            .order_by(Message.created_at.asc())
        )
        messages = result.scalars().all()
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    @staticmethod
    async def save_message(call_id: int, role: str, content: str, intent: str, db: AsyncSession) -> None:
        message = Message(
            call_id=call_id,
            role=role,
            content=content,
            intent=intent
        )
        db.add(message)
        await db.commit()
        logger.info(f"Saved call message log: call_id={call_id}, role={role}, intent={intent}")

    @staticmethod
    def load_prompt_file(filename: str) -> str:
        current_dir = os.path.dirname(os.path.dirname(__file__))
        filepath = os.path.join(current_dir, "prompts", filename)
        
        if not os.path.exists(filepath):
            logger.warning(f"Could not find prompt template: {filename}. Using default fallback.")
            return "You are a helpful voice AI agent."
            
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()

    @classmethod
    def compile_prompt(cls, intent: str = "general") -> str:
        base_prompt = cls.load_prompt_file("system_prompt.md")
        
        if intent == "sales":
            intent_prompt = cls.load_prompt_file("sales_prompt.md")
        elif intent == "support":
            intent_prompt = cls.load_prompt_file("support_prompt.md")
        elif intent == "booking":
            intent_prompt = cls.load_prompt_file("booking_prompt.md")
        else:
            intent_prompt = ""
            
        return f"{base_prompt}\n\n{intent_prompt}"
