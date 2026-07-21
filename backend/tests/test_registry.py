import pytest
from app.tools.registry import ToolRegistry
# Import tools to ensure registration decorators run
import app.tools as tools

def test_tool_registry_schemas() -> None:
    """Verifies that all annotated tools load their JSON schemas correctly."""
    definitions = ToolRegistry.get_tool_definitions(user_role="agent")
    tool_names = [tool["name"] for tool in definitions]
    
    # Assert core developer tools are registered
    assert "check_calendar_slots" in tool_names
    assert "create_crm_lead" in tool_names
    assert "book_appointment" in tool_names
    assert "send_confirmation_email" in tool_names
    
    # Verify parameter schemas exist
    calendar_tool = next(t for t in definitions if t["name"] == "check_calendar_slots")
    assert "date_str" in calendar_tool["parameters"]["properties"]
    assert calendar_tool["parameters"]["properties"]["date_str"]["type"] == "string"
