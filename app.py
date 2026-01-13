import eventlet
eventlet.monkey_patch()

import numpy as np
from collections import deque
from flask import Flask, render_template
from flask_socketio import SocketIO
from faster_whisper import WhisperModel

# ================= CONFIG =================
SAMPLE_RATE = 16000
WINDOW_SECONDS = 12.0
DECODE_INTERVAL = 1.8
MIN_AUDIO_SECONDS = 3.0
MAX_HISTORY = 300

# ================= APP ====================
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ================= WHISPER ===============
print("🔄 Loading Whisper model...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("✅ Whisper ready (ALL languages → English)")

# ================= STATE ==================
audio_buffer = np.zeros(0, dtype=np.float32)
audio_time_cursor = 0.0
emitted_segments = deque(maxlen=MAX_HISTORY)
listening = False
state_lock = eventlet.semaphore.Semaphore()

# ================= ROUTE ==================
@app.route("/")
def index():
    return render_template("index.html")

# ================= SOCKET =================
@socketio.on("toggle_listen")
def toggle_listen(data):
    global listening
    listening = data["state"]
    print(f"🎙 Listening: {listening}")

@socketio.on("audio_chunk")
def handle_audio_chunk(chunk):
    global audio_buffer, audio_time_cursor

    if not listening:
        return

    pcm = np.array(chunk, dtype=np.float32)

    with state_lock:
        audio_buffer = np.concatenate([audio_buffer, pcm])
        audio_time_cursor += len(pcm) / SAMPLE_RATE

        max_len = int(SAMPLE_RATE * WINDOW_SECONDS)
        if len(audio_buffer) > max_len:
            audio_buffer = audio_buffer[-max_len:]

# ================= DECODER LOOP ===========
def decode_loop():
    while True:
        eventlet.sleep(DECODE_INTERVAL)

        if not listening:
            continue

        with state_lock:
            if len(audio_buffer) < int(SAMPLE_RATE * MIN_AUDIO_SECONDS):
                continue

            audio = audio_buffer.copy()
            window_duration = len(audio) / SAMPLE_RATE
            window_start = audio_time_cursor - window_duration

        try:
            segments, info = model.transcribe(
                audio,
                task="translate",
                vad_filter=True,
                beam_size=5,
                temperature=0.0,
                word_timestamps=False,
                condition_on_previous_text=False
            )

            new_text = []

            with state_lock:
                for seg in segments:
                    text = seg.text.strip()
                    if not text:
                        continue

                    abs_start = round(window_start + seg.start, 2)
                    key = (abs_start, text)

                    if key not in emitted_segments:
                        emitted_segments.append(key)
                        new_text.append(text)

            if new_text:
                socketio.emit("subtitle", {"text": " ".join(new_text)})
                print(f"🌍 {info.language} → EN | {' '.join(new_text)}")

        except Exception as e:
            print(f"❌ Whisper error: {e}")

# ================= START ==================
eventlet.spawn(decode_loop)

if __name__ == "__main__":
    print("🚀 http://127.0.0.1:5000")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
