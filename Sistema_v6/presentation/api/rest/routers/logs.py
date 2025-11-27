import asyncio
import logging
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/logs", tags=["logs"])
logger = logging.getLogger(__name__)

LOG_FILE_PATH = Path("/tmp/sintaxis_backend.log")

@router.websocket("/ws")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Check if file exists
        if not LOG_FILE_PATH.exists():
            await websocket.send_text(f"Log file not found at {LOG_FILE_PATH}")
            await websocket.close()
            return

        # Open file and seek to end
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
            # Send last 20 lines initially
            lines = f.readlines()
            last_lines = lines[-20:] if len(lines) > 20 else lines
            for line in last_lines:
                await websocket.send_text(line.strip())
            
            # Seek to end to continue tailing
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    await websocket.send_text(line.strip())
                else:
                    await asyncio.sleep(0.1)
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected from log stream")
    except Exception as e:
        logger.error(f"Error streaming logs: {e}")
        try:
            await websocket.close()
        except:
            pass
