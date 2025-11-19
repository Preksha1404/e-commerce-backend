from fastapi import WebSocket, Query, Depends, APIRouter
from src.websockets.connection_manager import manager
from src.utils.auth import get_user_from_ws_token
from src.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.websocket("/ws/seller-notifications")
async def seller_notifications_ws(
    websocket: WebSocket, 
    token: str = Query(...), 
    db: Session = Depends(get_db)
):
    try:
        user = await get_user_from_ws_token(token, db)
    except Exception as e:
        print("Token validation failed:", e)
        await websocket.close(code=1008)
        return

    if user.role != "seller":
        await websocket.close(code=1008)
        return

    await manager.connect(user.id, websocket)

    try:
        while True:
            await websocket.receive_text()  # just keep connection alive
    except Exception as e:
        print("WebSocket disconnected:", e)
    finally:
        manager.disconnect(user.id, websocket)
