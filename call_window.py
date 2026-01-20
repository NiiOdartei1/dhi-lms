# call_window.py
"""
SocketIO handlers ONLY.

Do NOT create a Flask app here.
Do NOT initialize Session/db/migrate/mail/etc.

This module should only register event handlers against the
socketio instance exported from utils.extensions.
"""

import logging
from typing import Any, Dict, Optional

from flask_login import current_user
from utils.extensions import socketio

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def _user_id() -> str:
    """Helper: return a friendly id for logs."""
    try:
        if current_user and current_user.is_authenticated:
            return str(current_user.get_id() or "user")
    except Exception:
        pass
    return "guest"


@socketio.on("connect")
def handle_connect(auth: Optional[Dict[str, Any]] = None) -> None:
    """Client connected. auth is optional (used by some SocketIO clients)."""
    uid = _user_id()
    logger.info("Socket connected: %s (auth=%s)", uid, bool(auth))


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """Client disconnected."""
    uid = _user_id()
    logger.info("Socket disconnected: %s", uid)


@socketio.on("join_room")
def handle_join(data: Dict[str, Any]) -> None:
    """
    Request to join a room.
    data expected: {'room': 'room-name'}
    """
    room = data.get("room")
    if not room:
        logger.warning("join_room called without room by %s", _user_id())
        return
    socketio.enter_room(request.sid, room)  # type: ignore[name-defined]
    logger.info("User %s joined room %s", _user_id(), room)
    socketio.emit("room:joined", {"room": room}, room=room)


@socketio.on("leave_room")
def handle_leave(data: Dict[str, Any]) -> None:
    """Leave a room. data: {'room': 'room-name'}"""
    room = data.get("room")
    if not room:
        return
    socketio.leave_room(request.sid, room)  # type: ignore[name-defined]
    logger.info("User %s left room %s", _user_id(), room)
    socketio.emit("room:left", {"room": room}, room=room)


@socketio.on("call:start")
def start_call(data: Dict[str, Any]) -> None:
    """
    Start a call.
    Example data: {'room': 'class-1', 'caller': 'user_id', ...}
    Broadcasts 'call:started' to the room.
    """
    room = data.get("room")
    logger.info("call:start from %s room=%s data=%s", _user_id(), room, bool(data))
    if room:
        socketio.emit("call:started", data, room=room)
    else:
        # If no room provided, broadcast to all connected clients
        socketio.emit("call:started", data, broadcast=True)


@socketio.on("call:end")
def end_call(data: Dict[str, Any]) -> None:
    """
    End a call.
    Example data: {'room': 'class-1', 'caller': 'user_id', ...}
    """
    room = data.get("room")
    logger.info("call:end from %s room=%s", _user_id(), room)
    if room:
        socketio.emit("call:ended", data, room=room)
    else:
        socketio.emit("call:ended", data, broadcast=True)


@socketio.on("signal")
def handle_signal(data: Dict[str, Any]) -> None:
    """
    Generic signaling channel for WebRTC SDP/ICE exchange.
    Example data: {'to': socket_id_or_room, 'payload': {...}}
    """
    target = data.get("to")
    payload = data.get("payload")
    logger.debug("signal from %s to=%s", _user_id(), target)
    if not target:
        # If no explicit target, broadcast the payload
        socketio.emit("signal", {"from": _user_id(), "payload": payload}, broadcast=True)
        return

    # If target looks like a room name, emit to room, else emit to specific sid
    if isinstance(target, str) and target.startswith("room:"):
        room_name = target.split("room:", 1)[1]
        socketio.emit("signal", {"from": _user_id(), "payload": payload}, room=room_name)
    else:
        socketio.emit("signal", {"from": _user_id(), "payload": payload}, to=target)


# Export nothing else — this module only registers handlers when imported.
