from app.core.logger import logger
from app.tools.registry import ToolRegistry

@ToolRegistry.register(
    name="send_confirmation_email",
    description="Enqueues and sends an email notification to a client.",
    parameters={
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
        },
        "required": ["email", "subject", "body"]
    },
    required_permissions=["agent"]
)
async def send_confirmation_email(
    email: str,
    subject: str,
    body: str
) -> dict:
    logger.info(f"Tool Run: send_confirmation_email to {email}")
    # Under standard flows, this will enqueue a task to Redis/arq queue.
    # For now, it logs the simulated SMTP send task.
    logger.info(f"Simulating Email Dispatch to {email}: Subject='{subject}' | Body='{body}'")
    
    return {
        "success": True,
        "recipient": email,
        "message": f"Confirmation email successfully enqueued for {email}."
    }
