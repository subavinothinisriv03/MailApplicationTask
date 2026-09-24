"""WebSocket connection manager for real-time updates and assistant events."""
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket

logger = logging.getLogger("websocket")


class ConnectionManager:
    """Manages active WebSocket connections per user and broadcast channels."""

    def __init__(self):
        # Map user_id to set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Unauthenticated / guest connections
        self.anonymous_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: str = None):
        """Accept connection and register under user_id."""
        await websocket.accept()
        if user_id:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
            logger.info(f"WebSocket connected for user {user_id}")
        else:
            self.anonymous_connections.add(websocket)
            logger.info("Anonymous WebSocket connected")

    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """Unregister connection upon disconnection."""
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")
        else:
            self.anonymous_connections.discard(websocket)
            logger.info("Anonymous WebSocket disconnected")

    async def send_personal_message(self, message: Dict[str, Any], user_id: str):
        """Send event to all connections of a specific user."""
        if user_id in self.active_connections:
            dead_sockets = []
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send to socket: {e}")
                    dead_sockets.append(connection)
            for dead in dead_sockets:
                self.disconnect(dead, user_id)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        # Send to all users
        for user_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, user_id)
        # Send to anonymous
        dead_anonymous = []
        for connection in list(self.anonymous_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to anonymous socket: {e}")
                dead_anonymous.append(connection)
        for dead in dead_anonymous:
            self.anonymous_connections.discard(dead)

    async def emit_email_sent(self, email_data: Dict[str, Any], user_id: str):
        """Notify client that an email has been sent."""
        await self.send_personal_message({
            "type": "email_sent",
            "data": email_data
        }, user_id)

    async def emit_email_updated(self, email_data: Dict[str, Any], user_id: str):
        """Notify client that an email was updated (read/starred/labels)."""
        await self.send_personal_message({
            "type": "email_updated",
            "data": email_data
        }, user_id)

    async def emit_assistant_action(self, action_data: Dict[str, Any], user_id: str):
        """Notify client of an assistant event."""
        await self.send_personal_message({
            "type": "assistant_action",
            "data": action_data
        }, user_id)

    async def emit_tool_action(self, tool: str, arguments: Dict[str, Any], user_id: str, result: Any = None):
        """Broadcast structured tool execution to frontend."""
        await self.send_personal_message({
            "type": "tool_action",
            "tool": tool,
            "arguments": arguments,
            "result": result
        }, user_id)

    async def emit_typing(self, is_typing: bool, user_id: str):
        """Broadcast assistant typing state."""
        await self.send_personal_message({
            "type": "typing",
            "data": {"is_typing": is_typing}
        }, user_id)


ws_manager = ConnectionManager()
