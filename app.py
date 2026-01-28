import asyncio
import numpy as np
from collections import deque
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import socketio
from faster_whisper import WhisperModel
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
WINDOW_SECONDS = 12.0
DECODE_INTERVAL = 1.0  # Slightly faster interval for asyncio
MIN_AUDIO_SECONDS = 3.0
MAX_HISTORY = 300

# Constants for model management
DEFAULT_MODEL = "small"  # Upgraded from base to small for better accuracy/translation
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE = "int8"

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Global State
class GlobalState:
    def __init__(self):
        self.model = None
        self.audio_buffer = np.zeros(0, dtype=np.float32)
        self.audio_time_cursor = 0.0
        self.emitted_segments = deque(maxlen=MAX_HISTORY)
        self.listening = False
        self.lock = asyncio.Lock()
        self.current_model_name = DEFAULT_MODEL
        self.current_device = DEFAULT_DEVICE
        self.source_lang = None # None means auto-detect

state = GlobalState()

def load_model(model_size=DEFAULT_MODEL, device=DEFAULT_DEVICE):
    logger.info(f"Loading Whisper model: {model_size} on {device}...")
    try:
        # Use float16 on GPU, int8 on CPU for best performance/quality balance
        compute_type = "float16" if device == "cuda" else "int8"
        state.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        state.current_model_name = model_size
        state.current_device = device
        logger.info(f"Whisper model '{model_size}' ready on {device}")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        if device == "cuda":
            logger.info("Falling back to CPU...")
            load_model(model_size, "cpu")
        else:
            raise e

# Initialize model
load_model()

@sio.on("update_settings")
async def update_settings(sid, data):
    model_size = data.get("model", state.current_model_name)
    device = data.get("device", state.current_device)
    state.source_lang = data.get("language") if data.get("language") != "auto" else None
    
    if model_size != state.current_model_name or device != state.current_device:
        logger.info(f"Updating model: {model_size} on {device}")
        async with state.lock:
            state.audio_buffer = np.zeros(0, dtype=np.float32)
            load_model(model_size, device)
    
    logger.info(f"Settings updated: Model={state.current_model_name}, Device={state.current_device}, Lang={state.source_lang}")
    await sio.emit("settings_updated", {
        "model": state.current_model_name, 
        "device": state.current_device,
        "language": state.source_lang or "auto"
    }, to=sid)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/overlay", response_class=HTMLResponse)
async def overlay(request: Request):
    return templates.TemplateResponse("overlay.html", {"request": request})

@sio.on("toggle_listen")
async def toggle_listen(sid, data):
    state.listening = data["state"]
    if not state.listening:
        async with state.lock:
            state.audio_buffer = np.zeros(0, dtype=np.float32)
    logger.info(f"🎙 Listening: {state.listening}")

@sio.on("audio_chunk")
async def handle_audio_chunk(sid, chunk):
    if not state.listening:
        return

    pcm = np.array(chunk, dtype=np.float32)

    async with state.lock:
        state.audio_buffer = np.concatenate([state.audio_buffer, pcm])
        state.audio_time_cursor += len(pcm) / SAMPLE_RATE

        max_len = int(SAMPLE_RATE * WINDOW_SECONDS)
        if len(state.audio_buffer) > max_len:
            state.audio_buffer = state.audio_buffer[-max_len:]

async def decode_loop():
    logger.info("Starting transcription loop...")
    while True:
        await asyncio.sleep(DECODE_INTERVAL)

        if not state.listening:
            continue

        async with state.lock:
            if len(state.audio_buffer) < int(SAMPLE_RATE * MIN_AUDIO_SECONDS):
                return # Not enough audio yet

            audio = state.audio_buffer.copy()
            window_duration = len(audio) / SAMPLE_RATE
            window_start = state.audio_time_cursor - window_duration
            logger.info(f"Decoding {window_duration:.2f}s of audio (buffer size: {len(audio)})")

        try:
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None, 
                lambda: state.model.transcribe(
                    audio,
                    task="translate",
                    language=state.source_lang,
                    vad_filter=True,
                    beam_size=5,
                    temperature=0.0,
                    word_timestamps=True,
                    condition_on_previous_text=True,
                    initial_prompt="I am translating a live speech into English."
                )
            )

            seg_count = 0
            for seg in segments:
                seg_count += 1
                if seg.words:
                    for word in seg.words:
                        text = word.word.strip()
                        if not text:
                            continue
                        
                        abs_start = round(window_start + word.start, 2)
                        key = (abs_start, text)

                        if key not in state.emitted_segments:
                            state.emitted_segments.append(key)
                            await sio.emit("subtitle", {"text": text})
                            await asyncio.sleep(0.01) 
                else:
                    text = seg.text.strip()
                    if text:
                        abs_start = round(window_start + seg.start, 2)
                        key = (abs_start, text)
                        if key not in state.emitted_segments:
                            state.emitted_segments.append(key)
                            await sio.emit("subtitle", {"text": text})
            
            if seg_count == 0:
                logger.info("VAD detected silence/noise (no segments found)")
            else:
                logger.info(f"Detected {seg_count} segments")

        except Exception as e:
            logger.error(f" Whisper error: {e}")

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(decode_loop())

if __name__ == "__main__":
    import uvicorn
    print(" http://127.0.0.1:5000")
    # Using workers=1 because Whisper models are large and stateful
    uvicorn.run(socket_app, host="127.0.0.1", port=5000, log_level="info")
