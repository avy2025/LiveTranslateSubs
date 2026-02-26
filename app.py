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
import functools
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
WINDOW_SECONDS = 10.0
DECODE_INTERVAL = 0.8
MIN_AUDIO_SECONDS = 2.0 # Increased slightly to reduce noise fragments
MAX_HISTORY = 300

# Common Whisper hallucinations to filter out
HALLUCINATIONS = [
    "Thank you", "Thanks for watching", "Please subscribe", 
    "Subtitle by", "Subtitles by", "Bye", "bye", "you", "Thank you.",
    "Watching!", "Thanks.", "thank you"
]

# Constants for model management
DEFAULT_MODEL = "small"  # Reverted from large-v3-turbo because it may be too heavy for CPU
DEFAULT_DEVICE = "cpu"
DEFAULT_COMPUTE = "int8"

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load model and start transcription loop
    logger.info("Initializing system...")
    asyncio.create_task(decode_loop())
    # Load model in background to not block startup
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, load_model)
    
    # Heartbeat to keep connection alive and verify health
    async def heartbeat():
        while True:
            await sio.emit("heartbeat", {"status": "ok", "model_ready": state.model is not None})
            await asyncio.sleep(5)
    asyncio.create_task(heartbeat())
    
    yield
    # Shutdown logic (if any) could go here

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
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
        self.source_lang = "hi" # Defaulted to Hindi as per user request
        self.current_task = "translate" # Defaulted to Translate to English
        self.translation_cache = {} # Cache for translations

state = GlobalState()

def load_model(model_size=DEFAULT_MODEL, device=DEFAULT_DEVICE):
    logger.info(f"Loading Whisper model: {model_size} on {device}...")
    try:
        # Use float16 on GPU, int8 on CPU for best performance/quality balance
        compute_type = "float16" if device == "cuda" else "int8"
        state.model = WhisperModel(model_size, device=device, compute_type=compute_type, cpu_threads=4)
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
# model loading is now triggered in lifespan
# load_model() 

@sio.on("update_settings")
async def update_settings(sid, data):
    model_size = data.get("model", state.current_model_name)
    device = data.get("device", state.current_device)
    state.source_lang = data.get("language") if data.get("language") != "auto" else None
    state.current_task = data.get("task", state.current_task)
    
    if model_size != state.current_model_name or device != state.current_device:
        logger.info(f"Updating model: {model_size} on {device}")
        async with state.lock:
            state.audio_buffer = np.zeros(0, dtype=np.float32)
            load_model(model_size, device)
    
    logger.info(f"Settings updated: Model={state.current_model_name}, Device={state.current_device}, Lang={state.source_lang}, Task={state.current_task}")
    await sio.emit("settings_updated", {
        "model": state.current_model_name, 
        "device": state.current_device,
        "language": state.source_lang or "auto",
        "task": state.current_task
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

    if state.audio_time_cursor == 0:
        logger.info("📡 First audio chunk received")

    pcm = np.array(chunk, dtype=np.float32)

    async with state.lock:
        state.audio_buffer = np.concatenate([state.audio_buffer, pcm])
        state.audio_time_cursor += len(pcm) / SAMPLE_RATE
        # logger.info(f"Audio buffer expanded to {len(state.audio_buffer)} samples")

        max_len = int(SAMPLE_RATE * WINDOW_SECONDS)
        if len(state.audio_buffer) > max_len:
            state.audio_buffer = state.audio_buffer[-max_len:]

async def decode_loop():
    logger.info("Starting transcription loop...")
    while True:
        await asyncio.sleep(DECODE_INTERVAL)

        if not state.listening:
            # logger.info("Transcription loop: Not listening")
            continue

        if state.model is None:
            # logger.info("Waiting for model to load...")
            continue

        async with state.lock:
            buffer_needed = int(SAMPLE_RATE * MIN_AUDIO_SECONDS)
            if len(state.audio_buffer) < buffer_needed:
                # logger.info(f"Not enough audio: {len(state.audio_buffer)} < {buffer_needed}")
                continue 

            audio = state.audio_buffer.copy()
            window_duration = len(audio) / SAMPLE_RATE
            window_start = state.audio_time_cursor - window_duration
            
            # Check for silent audio (all zeros)
            if np.all(audio == 0):
                logger.warning("🔇 Audio buffer is completely silent (all zeros!)")
            
            logger.info(f"🔄 Decoding {window_duration:.2f}s (Buffer: {len(audio)})")

        try:
            # Better prompt to guide Hindi to English translation
            if state.current_task == "translate":
                prompt = "Transcribe and translate Hindi speech to English and keep it accurate. Context: real-time spoken Hindi."
            else:
                prompt = "Transcribe Hindi speech accurately."
            
            logger.info(f"Task: {state.current_task}, Lang Hint: {state.source_lang}")
            
            loop = asyncio.get_event_loop()
            segments, info = await loop.run_in_executor(
                None, 
                lambda: state.model.transcribe(
                    audio,
                    task=state.current_task,
                    language=state.source_lang,
                    vad_filter=True,
                    vad_parameters=dict(min_speech_duration_ms=400, threshold=0.4), # Stricter VAD
                    beam_size=5, 
                    temperature=0.0,
                    word_timestamps=True,
                    condition_on_previous_text=False, # Disabled to prevent "Thank you" loops
                    initial_prompt=prompt,
                    best_of=5,
                    no_speech_threshold=0.7, # Stricter on silence
                    log_prob_threshold=-1.0,
                    compression_ratio_threshold=2.4
                )
            )

            if info.language != state.source_lang:
                logger.info(f"🌍 Detected language: {info.language} (p={info.language_probability:.2f})")

            logger.info(f"Detected: {info.language} ({info.language_probability:.2f})")
            seg_count = 0
            for seg in segments:
                text = seg.text.strip()
                
                # Hallucination Filter
                if any(h.lower() in text.lower() for h in HALLUCINATIONS) and len(text.split()) < 4:
                    logger.info(f"🚫 Filtered hallucination: '{text}'")
                    continue

                seg_count += 1
                logger.info(f"📝 Segment {seg_count}: '{text}'")
                if seg.words:
                    for word in seg.words:
                        text = word.word.strip()
                        if not text:
                            continue
                        
                        abs_start = round(window_start + word.start, 2)
                        abs_end = round(window_start + word.end, 2)
                        key = (abs_start, text)

                        if key not in state.emitted_segments:
                            state.emitted_segments.append(key)
                            await sio.emit("subtitle", {
                                "text": text,
                                "start": abs_start,
                                "end": abs_end
                            })
                            await asyncio.sleep(0.01) 
                else:
                    text = seg.text.strip()
                    if text:
                        abs_start = round(window_start + seg.start, 2)
                        abs_end = round(window_start + seg.end, 2)
                        key = (abs_start, text)
                        if key not in state.emitted_segments:
                            state.emitted_segments.append(key)
                            await sio.emit("subtitle", {
                                "text": text,
                                "start": abs_start,
                                "end": abs_end
                            })
            
            if seg_count == 0:
                logger.info("VAD detected silence/noise (no segments found)")
                await sio.emit("vad_status", {"active": False})
            else:
                logger.info(f"Detected {seg_count} segments")
                await sio.emit("vad_status", {"active": True})

        except Exception as e:
            logger.error(f" Whisper error: {e}")

# Removed deprecated on_event("startup") - handled by lifespan

if __name__ == "__main__":
    import uvicorn
    print(" http://127.0.0.1:5000")
    # Using workers=1 because Whisper models are large and stateful
    uvicorn.run(socket_app, host="127.0.0.1", port=5000, log_level="info")
