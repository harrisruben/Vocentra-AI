import asyncio
from typing import Dict, List, Type, Callable, Any
from app.events.event_types import VocentraEvent
from app.core.logger import logger

class EventBus:
    """Async Event Bus Broker dispatching event payloads to subscribers."""
    _subscribers: Dict[Type[VocentraEvent], List[Callable[[Any], Any]]] = {}

    @classmethod
    def subscribe(cls, event_type: Type[VocentraEvent], handler: Callable[[Any], Any]) -> None:
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
        logger.info(f"EventBus: Subscribed handler '{handler.__name__}' to event '{event_type.__name__}'")

    @classmethod
    async def publish(cls, event: VocentraEvent) -> None:
        event_type = type(event)
        logger.info(f"EventBus: Publishing event '{event_type.__name__}' (event_id={event.event_id})")
        
        handlers = cls._subscribers.get(event_type, [])
        if not handlers:
            logger.info(f"EventBus: No subscribers found for event '{event_type.__name__}'")
            return
            
        tasks = []
        for handler in handlers:
            logger.info(f"EventBus: Dispatching '{event_type.__name__}' to subscriber '{handler.__name__}'")
            if asyncio.iscoroutinefunction(handler):
                tasks.append(handler(event))
            else:
                tasks.append(asyncio.to_thread(handler, event))
                
        if tasks:
            # Await all subscriber executions concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"EventBus: Subscriber '{handlers[idx].__name__}' failed: {str(res)}")
            
            logger.info(f"EventBus: Event '{event_type.__name__}' dispatch finalized to {len(tasks)} handlers.")
