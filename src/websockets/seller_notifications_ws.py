from fastapi import WebSocket, Query, APIRouter, Depends
from src.websockets.connection_manager import manager
from src.utils.auth import get_user_from_ws_token
from src.core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

@router.websocket("/ws/seller-notifications")
async def seller_notifications_ws(
    websocket: WebSocket,
    seller_id: int = Query(...),
    db: Session = Depends(get_db)
):
    # Accept connection to access cookies
    await websocket.accept()

    print(websocket)
    # Read token from HttpOnly cookie
    token = websocket.cookies.get("access_token")
    print(token)
    
    if not token:
        await websocket.close(code=1008)
        return

    # Validate token
    try:
        user = await get_user_from_ws_token(token, db)
    except Exception:
        await websocket.close(code=1008)
        return

    # Validate seller_id matches token owner
    if user.role != "seller" or user.id != seller_id:
        await websocket.close(code=1008)
        return

    # Connection is valid
    await manager.connect(seller_id, websocket)

    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        manager.disconnect(seller_id, websocket)
