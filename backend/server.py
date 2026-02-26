import asyncio
import numpy as np
import logging
import time
import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio

from backend import config
from backend.transcription.whisper_engine import get_whisper_engine
from backend.translation.translator import get_translator
from backend.audio.audio_buffer import AudioBuffer
from backend.subtitles.stabilizer import get_stabilizer
from backend.utils.text_merge import merge_overlap
from backend.transcription.model_selector import get_model_config

# Setup logging
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Socket.IO setup
sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins='*',
    max_http_buffer_size=100000000
)

class TranslationServer:
    def __init__(self):
        self.engine = None
        self.translator = None
        self.audio_buffer = AudioBuffer()
        self.stabilizer = get_stabilizer()
        self.is_listening = False
        self.model_config = get_model_config()
        self.current_offset_seconds = 0.0
        self.committed_text_hi = ""

    async def initialize(self):
        logger.info("Initializing Professional Speech Pipeline...")
        self.engine = get_whisper_engine()
        self.translator = get_translator()
        logger.info("System Ready.")

server_instance = TranslationServer()

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await server_instance.initialize()
    asyncio.create_task(processing_loop())
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Mount static and templates
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
templates = Jinja2Templates(directory=config.TEMPLATES_DIR)
socket_app = socketio.ASGIApp(sio, app)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@sio.on("connect")
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    from utils.hardware_detection import detect_hardware
    hw = detect_hardware()
    await sio.emit("status", {
        "model": server_instance.model_config["model_name"],
        "device": server_instance.model_config["device"],
        "ram": hw["ram_gb"],
        "ready": True
    }, to=sid)

@sio.on("toggle_microphone")
async def toggle_mic(sid, data):
    server_instance.is_listening = data.get("active", False)
    if not server_instance.is_listening:
        server_instance.audio_buffer.clear()
        server_instance.current_offset_seconds = 0.0
        server_instance.committed_text_hi = ""
        server_instance.stabilizer.clear()
    logger.info(f"Microphone toggled: {server_instance.is_listening}")

@sio.on("audio_data")
async def handle_audio(sid, chunk):
    if server_instance.is_listening:
        pcm = np.array(chunk, dtype=np.float32)
        logger.info(f"Received audio chunk: {len(pcm)} samples")
        server_instance.audio_buffer.add_chunk(pcm)

async def processing_loop():
    """
    Background loop for professional sliding window transcription and translation.
    """
    while True:
        await asyncio.sleep(0.5) 
        
        if not server_instance.is_listening:
            continue
            
        total_audio_len = server_instance.audio_buffer.get_total_duration()
        
        # Check window bounds
        window_start = server_instance.current_offset_seconds
        window_end = window_start + config.WINDOW_SIZE
        
        if window_end > total_audio_len:
            continue
            
        audio_window = server_instance.audio_buffer.get_window(window_start, config.WINDOW_SIZE)
        
        start_processing = time.time()
        try:
            # Stage 1: Hindi Transcription
            segments, info = server_instance.engine.transcribe(audio_window)
            window_text_hi = " ".join([seg.text.strip() for seg in segments if seg.text.strip()]).strip()
            
            if window_text_hi:
                logger.info(f"Window [{window_start:.1f}s - {window_end:.1f}s] Transcription: '{window_text_hi}'")
                
                # Overlap Merge (Deduplication)
                new_committed_hi = merge_overlap(server_instance.committed_text_hi, window_text_hi)
                
                if new_committed_hi != server_instance.committed_text_hi:
                    # Identify NEWLY transcribed text
                    added_text_hi = new_committed_hi[len(server_instance.committed_text_hi):].strip()
                    server_instance.committed_text_hi = new_committed_hi
                    
                    if added_text_hi:
                        # Stage 2: Text Translation (HI -> EN)
                        translation_en = server_instance.translator.translate(added_text_hi)
                        logger.info(f"Translation: '{translation_en}'")
                        
                        # Stage 3: Subtitle Stabilization
                        final_subtitle = server_instance.stabilizer.stabilize(translation_en)
                        
                        latency = (time.time() - start_processing) * 1000
                        
                        # Emit results to frontend
                        is_complete = server_instance.stabilizer.is_sentence_complete(final_subtitle)
                        await sio.emit("subtitle_update", {
                            "original": added_text_hi,
                            "translated": final_subtitle,
                            "type": "committed" if is_complete else "partial",
                            "latency": f"{latency:.0f}ms",
                            "buffer_size": f"{total_audio_len:.1f}s"
                        })

            # Advance Window
            server_instance.current_offset_seconds += config.WINDOW_STRIDE
            
        except Exception as e:
            logger.error(f"Error in professional processing loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host=config.HOST, port=config.PORT)
