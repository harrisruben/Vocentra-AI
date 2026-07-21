from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token
from app.core.logger import logger
import json

router = APIRouter(prefix="/ws", tags=["WebSockets"])

class WebSocketConnectionManager:
    def __init__(self):
        # org_id (int) -> list of dashboard websockets
        self.dashboard_connections: Dict[int, List[WebSocket]] = {}
        # vapi_call_id (str) -> list of transcript websockets
        self.transcript_connections: Dict[str, List[WebSocket]] = {}
        # org_id (int) -> list of general call alerts websockets
        self.call_alert_connections: Dict[int, List[WebSocket]] = {}

    # Dashboard WebSocket channels
    async def connect_dashboard(self, websocket: WebSocket, org_id: int):
        await websocket.accept()
        if org_id not in self.dashboard_connections:
            self.dashboard_connections[org_id] = []
        self.dashboard_connections[org_id].append(websocket)
        logger.info(f"WS-Dashboard: Client connected to org {org_id}. Total: {len(self.dashboard_connections[org_id])}")

    def disconnect_dashboard(self, websocket: WebSocket, org_id: int):
        if org_id in self.dashboard_connections:
            if websocket in self.dashboard_connections[org_id]:
                self.dashboard_connections[org_id].remove(websocket)
            if not self.dashboard_connections[org_id]:
                del self.dashboard_connections[org_id]
        logger.info(f"WS-Dashboard: Client disconnected from org {org_id}")

    async def broadcast_dashboard(self, org_id: int, message: dict):
        if org_id in self.dashboard_connections:
            logger.info(f"WS-Dashboard: Broadcasting message to org {org_id} ({len(self.dashboard_connections[org_id])} clients)")
            dead = []
            for connection in self.dashboard_connections[org_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"WS-Dashboard fail: {str(e)}")
                    dead.append(connection)
            for connection in dead:
                self.disconnect_dashboard(connection, org_id)

    # Transcript WebSocket channels (scoped to call_id)
    async def connect_transcript(self, websocket: WebSocket, call_id: str):
        await websocket.accept()
        if call_id not in self.transcript_connections:
            self.transcript_connections[call_id] = []
        self.transcript_connections[call_id].append(websocket)
        logger.info(f"WS-Transcript: Client connected to call {call_id}. Total: {len(self.transcript_connections[call_id])}")

    def disconnect_transcript(self, websocket: WebSocket, call_id: str):
        if call_id in self.transcript_connections:
            if websocket in self.transcript_connections[call_id]:
                self.transcript_connections[call_id].remove(websocket)
            if not self.transcript_connections[call_id]:
                del self.transcript_connections[call_id]
        logger.info(f"WS-Transcript: Client disconnected from call {call_id}")

    async def broadcast_transcript(self, call_id: str, message: dict):
        if call_id in self.transcript_connections:
            logger.info(f"WS-Transcript: Broadcasting transcript update to call {call_id} ({len(self.transcript_connections[call_id])} clients)")
            dead = []
            for connection in self.transcript_connections[call_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"WS-Transcript fail: {str(e)}")
                    dead.append(connection)
            for connection in dead:
                self.disconnect_transcript(connection, call_id)

    # General Call Alert WebSocket channels (scoped to organization)
    async def connect_calls(self, websocket: WebSocket, org_id: int):
        await websocket.accept()
        if org_id not in self.call_alert_connections:
            self.call_alert_connections[org_id] = []
        self.call_alert_connections[org_id].append(websocket)
        logger.info(f"WS-Calls: Client connected to org {org_id}. Total: {len(self.call_alert_connections[org_id])}")

    def disconnect_calls(self, websocket: WebSocket, org_id: int):
        if org_id in self.call_alert_connections:
            if websocket in self.call_alert_connections[org_id]:
                self.call_alert_connections[org_id].remove(websocket)
            if not self.call_alert_connections[org_id]:
                del self.call_alert_connections[org_id]
        logger.info(f"WS-Calls: Client disconnected from org {org_id}")

    async def broadcast_call_event(self, org_id: int, message: dict):
        if org_id in self.call_alert_connections:
            logger.info(f"WS-Calls: Broadcasting call state transition to org {org_id} ({len(self.call_alert_connections[org_id])} clients)")
            dead = []
            for connection in self.call_alert_connections[org_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"WS-Calls fail: {str(e)}")
                    dead.append(connection)
            for connection in dead:
                self.disconnect_calls(connection, org_id)

manager = WebSocketConnectionManager()

@router.websocket("/dashboard")
async def ws_dashboard(websocket: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if not payload:
        logger.warning("Rejected WS-Dashboard connection: Invalid JWT token.")
        await websocket.close(code=1008)
        return
    org_id = payload.get("organization_id")
    if not org_id:
        logger.warning("Rejected WS-Dashboard connection: No organization_id in token.")
        await websocket.close(code=1008)
        return

    await manager.connect_dashboard(websocket, org_id)
    try:
        while True:
            # Keep socket alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_dashboard(websocket, org_id)
    except Exception as e:
        logger.error(f"WS-Dashboard Exception: {str(e)}")
        manager.disconnect_dashboard(websocket, org_id)

@router.websocket("/transcripts")
async def ws_transcripts(websocket: WebSocket, call_id: str = Query(...), token: str = Query(...)):
    payload = decode_access_token(token)
    if not payload:
        logger.warning("Rejected WS-Transcript connection: Invalid JWT token.")
        await websocket.close(code=1008)
        return

    await manager.connect_transcript(websocket, call_id)
    try:
        while True:
            # Keep socket alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_transcript(websocket, call_id)
    except Exception as e:
        logger.error(f"WS-Transcript Exception: {str(e)}")
        manager.disconnect_transcript(websocket, call_id)

@router.websocket("/calls")
async def ws_calls(websocket: WebSocket, token: str = Query(...)):
    payload = decode_access_token(token)
    if not payload:
        logger.warning("Rejected WS-Calls connection: Invalid JWT token.")
        await websocket.close(code=1008)
        return
    org_id = payload.get("organization_id")
    if not org_id:
        logger.warning("Rejected WS-Calls connection: No organization_id in token.")
        await websocket.close(code=1008)
        return

    await manager.connect_calls(websocket, org_id)
    try:
        while True:
            # Keep socket alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_calls(websocket, org_id)
    except Exception as e:
        logger.error(f"WS-Calls Exception: {str(e)}")
        manager.disconnect_calls(websocket, org_id)
