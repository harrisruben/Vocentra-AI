from typing import Dict, List, Callable, Any, Optional
from pydantic import BaseModel
from app.core.logger import logger

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict # JSON schema description of parameters
    required_permissions: List[str] = ["agent"] # Required RBAC roles to invoke

class ToolRegistry:
    """Enterprise Tool Registry executing Python actions and validating RBAC permissions."""
    _registry: Dict[str, tuple[ToolDefinition, Callable[..., Any]]] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        parameters: dict,
        required_permissions: Optional[List[str]] = None
    ) -> Callable[..., Any]:
        """Decorator binding a python method with parameters schema in the registry."""
        permissions = required_permissions or ["agent"]
        
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            definition = ToolDefinition(
                name=name,
                description=description,
                parameters=parameters,
                required_permissions=permissions
            )
            cls._registry[name] = (definition, func)
            logger.info(f"ToolRegistry: Registered action '{name}' (required_permissions={permissions})")
            return func
        return decorator

    @classmethod
    def get_tool_definitions(cls, user_role: str = "agent") -> List[dict]:
        """Compiles schemas matching user permission levels (suited for LLM function lists)."""
        active_tools = []
        for name, (definition, _) in cls._registry.items():
            # Standard matching: Owner overrides Manager, Manager overrides Agent
            if (
                user_role == "owner" or
                (user_role == "manager" and "owner" not in definition.required_permissions) or
                (user_role == "agent" and "owner" not in definition.required_permissions and "manager" not in definition.required_permissions) or
                "agent" in definition.required_permissions
            ):
                active_tools.append(definition.model_dump())
        return active_tools

    @classmethod
    async def execute_tool(cls, name: str, user_role: str, *args, **kwargs) -> Any:
        """Executes a tool after performing role-based security validation."""
        if name not in cls._registry:
            raise KeyError(f"Tool '{name}' not found in the registry.")
            
        definition, func = cls._registry[name]
        
        # Verify RBAC permissions
        allowed_roles = definition.required_permissions
        if "agent" not in allowed_roles: # custom restriction
            if user_role not in allowed_roles:
                logger.warning(f"ToolRegistry: Unauthorized attempt to execute '{name}' under role '{user_role}'")
                raise PermissionError(f"Access denied. User role '{user_role}' cannot run tool '{name}'.")
                
        logger.info(f"ToolRegistry: Invoking '{name}' for caller with role '{user_role}'")
        return await func(*args, **kwargs)
