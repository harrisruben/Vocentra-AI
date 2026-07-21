import datetime
from app.core.logger import logger
from app.tools.registry import ToolRegistry

@ToolRegistry.register(
    name="check_calendar_slots",
    description="Check for available appointment times for a specific date (format YYYY-MM-DD).",
    parameters={
        "type": "object",
        "properties": {
            "date_str": {"type": "string", "description": "Target date string in YYYY-MM-DD format."}
        },
        "required": ["date_str"]
    },
    required_permissions=["agent"]
)
async def check_calendar_slots(date_str: str) -> dict:
    logger.info(f"Tool Run: check_calendar_slots for {date_str}")
    
    try:
        # Validate date format (YYYY-MM-DD)
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Failed to parse target booking date: {date_str}")
        return {
            "success": False,
            "message": "Invalid date string format. Use YYYY-MM-DD (e.g., '2026-07-15')."
        }
        
    # Return available scheduling slots
    mock_slots = ["10:00 AM", "1:30 PM", "3:30 PM"]
    logger.info(f"Available slots for {date_str}: {mock_slots}")
    
    return {
        "success": True,
        "date": date_str,
        "slots": mock_slots,
        "message": f"Available slots on {date_str} are: 10:00 AM, 1:30 PM, and 3:30 PM."
    }
