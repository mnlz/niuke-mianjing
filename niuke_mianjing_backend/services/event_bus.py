import asyncio
from typing import Callable, Dict, List, Any
from niuke_mianjing_backend.schemas.ws import WSMessage, WSMessageType


class EventBus:
    _instance = None
    _listeners: Dict[WSMessageType, List[Callable]] = None
    _ws_connections: List = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._listeners = {}
            cls._instance._ws_connections = []
        return cls._instance

    def subscribe(self, event_type: WSMessageType, callback: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: WSMessageType, callback: Callable):
        if event_type in self._listeners:
            self._listeners[event_type] = [cb for cb in self._listeners[event_type] if cb != callback]

    async def publish(self, event_type: WSMessageType, data: Any = None, message: str = None):
        ws_msg = WSMessage(type=event_type, data=data, message=message)

        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(ws_msg)
                    else:
                        callback(ws_msg)
                except Exception as e:
                    print(f"EventBus listener error: {e}")

        await self._broadcast_ws(ws_msg)

    def add_ws_connection(self, websocket):
        self._ws_connections.append(websocket)

    def remove_ws_connection(self, websocket):
        self._ws_connections = [ws for ws in self._ws_connections if ws != websocket]

    async def _broadcast_ws(self, msg: WSMessage):
        disconnected = []
        for ws in self._ws_connections:
            try:
                await ws.send_json(msg.model_dump(mode="json"))
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            self._ws_connections.remove(ws)

    @classmethod
    def reset(cls):
        if cls._instance:
            cls._instance._listeners = {}
            cls._instance._ws_connections = []
