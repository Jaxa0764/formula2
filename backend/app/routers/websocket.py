import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.connection_manager import manager

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger("smartfuel.websocket")

@router.websocket("/websocket")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time station updates, price changes,
    CNG pressure fluctuations, and administrative alerts.
    """
    await manager.connect(websocket)
    try:
        # Send initial welcome / connection ack
        await websocket.send_text(json.dumps({
            "type": "CONNECTION_ESTABLISHED",
            "message": "Real-time SmartFuel UZ feed connected"
        }))
        while True:
            data = await websocket.receive_text()
            # Handle client ping or subscription messages
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
