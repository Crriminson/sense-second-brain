from typing import List, Callable, Dict

# Event bus (WebSocket manager)

class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)

    async def emit(self, event_type: str, data: dict):
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                await handler(data)

event_bus = EventBus()
