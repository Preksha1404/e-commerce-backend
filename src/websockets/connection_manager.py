from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: Dict[int, List[WebSocket]] = {}  # seller_id -> websockets list

    async def connect(self, seller_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(seller_id, []).append(websocket)

    def disconnect(self, seller_id: int, websocket: WebSocket):
        conns = self.connections.get(seller_id)
        if not conns:
            return
        try:
            conns.remove(websocket)
            if not conns:
                self.connections.pop(seller_id, None)
        except ValueError:
            pass

    async def send_to_seller(self, seller_id: int, message: dict):
        conns = self.connections.get(seller_id, [])
        for ws in conns.copy():
            try:
                await ws.send_json(message)
            except Exception:
                try:
                    await ws.close()
                except:
                    pass
                self.disconnect(seller_id, ws)

# Single shared instance
manager = ConnectionManager()
