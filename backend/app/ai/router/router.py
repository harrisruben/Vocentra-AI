from app.ai.router.sales import SALES_PROMPT
from app.ai.router.support import SUPPORT_PROMPT
from app.core.logger import logger

class MultiAgentRouter:
    """Enterprise Routing Engine that dynamically transitions conversations between specialized agents."""
    
    _agents = {
        "sales": SALES_PROMPT,
        "support": SUPPORT_PROMPT,
        "general": (
            "You are Vocentra's primary voice receptionist. "
            "Greet the caller, understand their query, and guide them to either our Sales division "
            "(for subscription tiers, demos, and pricing) or Support division (for technical troubleshooting)."
        )
    }

    @classmethod
    def get_agent_prompt(cls, agent_name: str) -> str:
        """Returns prompt string associated with agent name."""
        return cls._agents.get(agent_name, cls._agents["general"])

    @classmethod
    def route_message(cls, message: str, current_agent: str = "general") -> str:
        """Analyzes caller speech input and triggers intent state transitions."""
        if not message:
            return current_agent
            
        text = message.lower().strip()
        logger.info(f"MultiAgentRouter: Scanning user text: '{text}' (Active Agent: '{current_agent}')")
        
        # Check transition to Sales Agent
        sales_keywords = ["price", "pricing", "cost", "demo", "buy", "purchase", "enterprise", "sales", "quote"]
        if any(keyword in text for keyword in sales_keywords):
            if current_agent != "sales":
                logger.info("MultiAgentRouter: Transitioning conversation state to -> 'sales'")
            return "sales"
            
        # Check transition to Support Agent
        support_keywords = ["support", "help", "broken", "error", "bug", "ticket", "issue", "troubleshoot", "status"]
        if any(keyword in text for keyword in support_keywords):
            if current_agent != "support":
                logger.info("MultiAgentRouter: Transitioning conversation state to -> 'support'")
            return "support"
            
        # Remain in current conversation state if no indicators match
        return current_agent
