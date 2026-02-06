import logging
from typing import Dict, List, Callable, Optional

logger = logging.getLogger(__name__)

class EventDispatcher:
    """
    Decoupled In-Memory Event Dispatcher (Pub/Sub).
    Supports localized filters (e.g. subscribing only to a specific ontology).
    """
    _subscribers: Dict[str, List[Dict]] = {}

    @classmethod
    def subscribe(cls, event_name: str, callback: Callable, ontology_filter: Optional[str] = None):
        """Register a subscriber for a specific event."""
        if event_name not in cls._subscribers:
            cls._subscribers[event_name] = []
        
        cls._subscribers[event_name].append({
            "callback": callback,
            "filter": ontology_filter
        })
        logger.info(f"Subscribed to event '{event_name}' (filter: {ontology_filter})")

    @classmethod
    def dispatch(cls, event_name: str, payload: dict):
        """Dispatch an event to all matching subscribers."""
        if event_name not in cls._subscribers:
            return

        ontology_name = payload.get("name")
        for sub in cls._subscribers[event_name]:
            callback = sub["callback"]
            wh_filter = sub["filter"]

            # Filter logic: global subscription or name match
            if not wh_filter or wh_filter == ontology_name:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"Error in subscriber for {event_name}: {e}")

# Global instance for easy access (Singleton pattern)
dispatcher = EventDispatcher()
