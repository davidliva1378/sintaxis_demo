import asyncio
import websockets
import sys

async def test_ws():
    uri = "ws://localhost:8000/api/v1/extraccion-masiva/sesion/fake-session-id/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected")
            msg = await websocket.recv()
            print(f"Received: {msg}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e.code} {e.reason}")
        if e.code == 4004:
            print("SUCCESS: Correctly rejected invalid session")
            sys.exit(0)
        else:
            print(f"FAILURE: Unexpected close code {e.code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_ws())
