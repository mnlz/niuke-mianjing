from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from niuke_mianjing_backend.api.security import is_valid_admin_token
from niuke_mianjing_backend.services.event_bus import EventBus
from niuke_mianjing_backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/api/ws/crawl")
async def websocket_crawl(websocket: WebSocket):
    if not is_valid_admin_token(websocket.query_params.get("token")):
        await websocket.close(code=4401, reason="Unauthorized")
        return
    await websocket.accept()
    event_bus = EventBus()
    event_bus.add_ws_connection(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.remove_ws_connection(websocket)
        logger.info("WebSocket 客户端断开连接，当前连接数: %d", len(event_bus._ws_connections))


@router.websocket("/api/ws")
async def websocket_general(websocket: WebSocket):
    if not is_valid_admin_token(websocket.query_params.get("token")):
        await websocket.close(code=4401, reason="Unauthorized")
        return
    await websocket.accept()
    event_bus = EventBus()
    event_bus.add_ws_connection(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        event_bus.remove_ws_connection(websocket)
        logger.info("WebSocket 客户端断开连接，当前连接数: %d", len(event_bus._ws_connections))
