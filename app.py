import os
import sys

# Maintain compatibility with previous entry point
if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    from backend.server import socket_app
    import uvicorn
    from backend import config
    
    print(f"🚀 Starting LiveTranslateSubs via app.py on http://{config.HOST}:{config.PORT}")
    uvicorn.run(socket_app, host=config.HOST, port=config.PORT, log_level="info")
