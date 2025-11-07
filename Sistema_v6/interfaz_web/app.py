import threading
import webview
import uvicorn
from backend.main import app



def iniciar_backend():
    uvicorn.run(app, host="127.0.0.1", port=8001)

if __name__ == "__main__":
    threading.Thread(target=iniciar_backend, daemon=True).start()
    webview.create_window("Sistema Jurídico", "http://127.0.0.1:8001")
    webview.start()
