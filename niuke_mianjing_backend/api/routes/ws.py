from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from niuke_mianjing_backend.services.event_bus import EventBus
from niuke_mianjing_backend.schemas.ws import WSMessage


router = APIRouter(tags=["WebSocket"])


@router.websocket("/api/ws/crawl")
async def websocket_crawl(websocket: WebSocket):
    await websocket.accept()
    event_bus = EventBus()
    event_bus.add_ws_connection(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.remove_ws_connection(websocket)
        print(f"WebSocket 客户端断开连接，当前连接数: {len(event_bus._ws_connections)}")


@router.websocket("/api/ws")
async def websocket_general(websocket: WebSocket):
    await websocket.accept()
    event_bus = EventBus()
    event_bus.add_ws_connection(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.remove_ws_connection(websocket)
        print(f"WebSocket 客户端断开连接，当前连接数: {len(event_bus._ws_connections)}")
