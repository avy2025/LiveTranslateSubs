import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from backend.server import socket_app
    import uvicorn
    from backend import config
    
    print(f"🚀 Starting LiveTranslateSubs on http://{config.HOST}:{config.PORT}")
    uvicorn.run(socket_app, host=config.HOST, port=config.PORT, log_level="info")
