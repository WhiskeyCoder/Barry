from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/stream")
async def stream(websocket: WebSocket) -> None:
    await websocket.accept()
    engine = websocket.app.state.engine  # type: ignore[attr-defined]
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            action = msg.get("action", "step")
            brain_id = UUID(msg["brain_id"])
            brain = engine.brains.get(brain_id)
            if action == "inject":
                brain.sensors.set(msg["channel"], msg["data"])
            ms = float(msg.get("milliseconds", 10))
            brain.step(ms)
            await websocket.send_json(
                {
                    "time_ms": brain.network._state.time_ms,
                    "motors": brain.motors.decode_all(brain.network),
                    "spikes": int(brain.network._state.spikes.sum()),
                }
            )
    except (WebSocketDisconnect, KeyError, ValueError):
        await websocket.close()
