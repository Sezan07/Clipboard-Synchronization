from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
app = FastAPI()
# Enable CORS (optional but helpful for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[""],
    allow_credentials=True,
    allow_methods=[""],
    allow_headers=["*"],
)
# In-memory session store: {session_id: {"clients": [WebSocket, ...], "clipboard": str}}
sessions = {}
@app.get("/")
def root():
    return {"status": "WebSocket server ready"}
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    # Create session if it doesn't exist
    if session_id not in sessions:
        sessions[session_id] = {"clients": [], "clipboard": ""}
    sessions[session_id]["clients"].append(websocket)
    print(f"[+] {session_id}: Client connected. Total: {len(sessions[session_id]['clients'])}")
    # On connect, send last known clipboard state
    clipboard_data = sessions[session_id]["clipboard"]
    if clipboard_data:
        await websocket.send_text(clipboard_data)
    try:
        while True:
            data = await websocket.receive_text()
            sessions[session_id]["clipboard"] = data
            print(f"[→] {session_id}: Received update")
            for client in sessions[session_id]["clients"]:
                if client != websocket:
                    try:
                        await client.send_text(data)
                    except:
                        pass  # Handle silently
    except WebSocketDisconnect:
        sessions[session_id]["clients"].remove(websocket)
        print(f"[-] {session_id}: Client disconnected. Remaining: {len(sessions[session_id]['clients'])}")
        if not sessions[session_id]["clients"]:
            del sessions[session_id]
            print(f"[x] {session_id}: Session closed (no clients)")
# Optional: for local testing
if name == "main":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
