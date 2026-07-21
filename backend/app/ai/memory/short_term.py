from app.voice.session_manager import SessionManager

class ShortTermMemory:
    """Short-term active call variables context tracker."""
    
    @staticmethod
    def get_call_state(call_sid: str) -> dict:
        return SessionManager.get_session(call_sid)
        
    @staticmethod
    def save_variable(call_sid: str, key: str, value: str) -> None:
        SessionManager.save_slot(call_sid, key, value)
        
    @staticmethod
    def clear_call_state(call_sid: str) -> None:
        SessionManager.clear_session(call_sid)
