import time
import json
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from nudge_engine import NudgeController

app = FastAPI(title="Q4 Real-Time Nudge Pipeline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

controller = NudgeController(cooldown_seconds=15.0)


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    Expects JSON messages of shape {"transcript": str, "speaker": "agent"|"customer"}.
    In production these come from streaming ASR partial/final results; for local
    testing, replay_transcript.py sends them from a transcript file at
    real-time pace to simulate a live call.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            received_at = time.time()
            nudge, latency_ms = controller.evaluate_transcript(
                payload.get("transcript", ""), payload.get("speaker", ""), now=received_at
            )
            if nudge:
                await websocket.send_json(nudge)
    except WebSocketDisconnect:
        print("WebSocket disconnected")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
