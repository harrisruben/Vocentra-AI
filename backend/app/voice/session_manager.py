from app.core.logger import logger

class SessionManager:
    # In-memory transient session states (can be backed by Redis in production compose environments)
    _sessions = {}

    @classmethod
    def get_session(cls, call_sid: str) -> dict:
        if call_sid not in cls._sessions:
            cls._sessions[call_sid] = {
                "active_intent": "general",
                "slots": {},
                "tool_outputs": [],
                "caller_name": None,
                "caller_email": None
            }
        return cls._sessions[call_sid]

    @classmethod
    def detect_intent(cls, call_sid: str, user_speech: str) -> str:
        session = cls.get_session(call_sid)
        text = user_speech.lower()
        
        previous_intent = session["active_intent"]
        detected_intent = previous_intent
        
        # Keyword triggers
        if any(w in text for w in ["pricing", "price", "rate", "sales", "cost", "quote"]):
            detected_intent = "sales"
        elif any(w in text for w in ["book", "schedule", "appointment", "demo", "calendar", "reserve"]):
            detected_intent = "booking"
        elif any(w in text for w in ["help", "support", "faq", "issue", "question", "work"]):
            detected_intent = "support"
            
        if detected_intent != previous_intent:
            logger.info(f"Call Session [{call_sid}]: Intent shifted from '{previous_intent}' to '{detected_intent}'")
            session["active_intent"] = detected_intent
            
        return detected_intent

    @classmethod
    def save_slot(cls, call_sid: str, key: str, value: str) -> None:
        session = cls.get_session(call_sid)
        session["slots"][key] = value
        logger.info(f"Call Session [{call_sid}]: Captured slot '{key}' = '{value}'")

    @classmethod
    def clear_session(cls, call_sid: str) -> None:
        if call_sid in cls._sessions:
            del cls._sessions[call_sid]
            logger.info(f"Call Session [{call_sid}]: Cleared active state cache")
