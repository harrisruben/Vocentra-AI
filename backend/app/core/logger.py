import logging
import sys
from contextvars import ContextVar
from typing import Optional

# Context variable to track Request ID across async task boundaries
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_var.get() or "SYSTEM"
        asctime = self.formatTime(record, self.datefmt)
        log_msg = f"[{asctime}] [{record.levelname}] [req-id: {req_id}] [{record.name}] {record.getMessage()}"
        if record.exc_info:
            log_msg += "\n" + self.formatException(record.exc_info)
        return log_msg

def setup_logger(name: str = "vocentra") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger

logger = setup_logger("vocentra")
