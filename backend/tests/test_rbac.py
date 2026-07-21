import pytest
from app.tools.registry import ToolRegistry

@pytest.mark.asyncio
async def test_tool_registry_rbac_boundaries() -> None:
    """Verifies that low-permission user roles are blocked from high-security tools."""
    
    # Register custom high-security test action
    @ToolRegistry.register(
        name="owner_only_wipe_database",
        description="Destructive action requiring Owner permissions.",
        parameters={},
        required_permissions=["owner"]
    )
    async def mock_wipe_db() -> str:
        return "database_wiped"
        
    # 1. Verify Owner role successfully bypasses checker
    response = await ToolRegistry.execute_tool("owner_only_wipe_database", user_role="owner")
    assert response == "database_wiped"
    
    # 2. Verify Agent role is blocked and raises PermissionError
    with pytest.raises(PermissionError) as exc_info:
        await ToolRegistry.execute_tool("owner_only_wipe_database", user_role="agent")
        
    assert "Access denied. User role 'agent' cannot run tool" in str(exc_info.value)
