import pytest
from app.ai.router.router import MultiAgentRouter
from app.ai.router.sales import SALES_PROMPT
from app.ai.router.support import SUPPORT_PROMPT

def test_multi_agent_routing() -> None:
    """Verifies user messages transition conversational state between agents."""
    # 1. Verify Sales routing
    assert MultiAgentRouter.route_message("What is the cost of your enterprise tier?") == "sales"
    assert MultiAgentRouter.route_message("I'd like to book a product demo.") == "sales"
    
    # 2. Verify Support routing
    assert MultiAgentRouter.route_message("My dashboard is showing a connection error.") == "support"
    assert MultiAgentRouter.route_message("Help, my webhook is broken!") == "support"
    
    # 3. Verify Default routing
    assert MultiAgentRouter.route_message("Good morning!") == "general"
    
    # 4. Verify Prompt retrieval
    assert MultiAgentRouter.get_agent_prompt("sales") == SALES_PROMPT
    assert MultiAgentRouter.get_agent_prompt("support") == SUPPORT_PROMPT
