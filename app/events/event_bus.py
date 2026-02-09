from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._handlers: dict[type, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable):
        self._handlers[event_type].append(handler)

    async def emit(self, event: Any):
        for handler in self._handlers[type(event)]:
            await handler(event)


event_bus = EventBus()