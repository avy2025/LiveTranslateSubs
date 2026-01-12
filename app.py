import base64
import numpy as np
from flask import Flask
from flask_socketio import SocketIO, emit
from faster_whisper import WhisperModel
import threading
import time

# ================== CONFIG ==================
SAMPLE_RATE = 16000
CHUNK_SECONDS = 2.0

# ================== APP ==================
app = Flask(__name__)
app.config["SECRET_KEY"] = "live-translate"
socketio = SocketIO(app, cors_allowed_origins="*")

# ================== WHISPER ==================
print("🔄 Loading Whisper model...")
model = WhisperModel("tiny", device="cpu", compute_type="int8")
print("✅ Whisper ready")

# ================== AUDIO STATE ==================
audio_buffer = []
buffer_lock = threading.Lock()

# ================== FRONTEND ==================
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Live Translate Subs</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>

<style>
body {
    background:#0e0e0e;
    color:#00ff9c;
    font-family:Arial;
    text-align:center;
}
button {
    padding:12px 28px;
    font-size:18px;
    border-radius:25px;
    border:none;
    cursor:pointer;
}
#status {
    margin-top:15px;
    color:#ccc;
}
#subs {
    margin:20px auto;
    width:80%;
    min-height:200px;
    background:#000;
    padding:15px;
    border-radius:10px;
    font-size:22px;
}
</style>
</head>

<body>
<h2>🎤 Live Multilingual → English</h2>
<button id="start">Start</button>
<p id="status">Idle</p>
<div id="subs"></div>

<script>
const socket = io();
let audioCtx, source, processor;
let running = false;

document.getElementById("start").onclick = async () => {
    if (running) return;

    running = true;
    document.getElementById("status").innerText = "Listening...";

    const stream = await navigator.mediaDevices.getUserMedia({ audio:true });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate:16000 });

    source = audioCtx.createMediaStreamSource(stream);
    processor = audioCtx.createScriptProcessor(4096, 1, 1);

    source.connect(processor);
    processor.connect(audioCtx.destination);

    processor.onaudioprocess = e => {
        if (!running) return;
        const input = e.inputBuffer.getChannelData(0);
        const bytes = new Uint8Array(input.buffer);
        const b64 = btoa(String.fromCharCode(...bytes));
        socket.emit("audio", b64);
    };
};

socket.on("subtitle", data => {
    const el = document.getElementById("subs");
    el.innerHTML += " " + data.text;
    el.scrollTop = el.scrollHeight;
});
</script>
</body>
</html>
"""

# ================== SOCKET ==================
@socketio.on("audio")
def handle_audio(b64):
    global audio_buffer

    try:
        pcm = np.frombuffer(base64.b64decode(b64), dtype=np.float32)

        with buffer_lock:
            audio_buffer.append(pcm)
            total = sum(len(x) for x in audio_buffer)

            if total >= int(SAMPLE_RATE * CHUNK_SECONDS):
                audio = np.concatenate(audio_buffer)
                audio_buffer.clear()

        if 'audio' in locals():
            segments, info = model.transcribe(
                audio,
                task="translate",
                vad_filter=True
            )

            text = " ".join(s.text.strip() for s in segments if s.text.strip())
            if text:
                emit("subtitle", {"text": text})
                print(f"🌍 {info.language} → EN | {text}")

    except Exception as e:
        print("❌ Error:", e)
        audio_buffer.clear()

# ================== RUN ==================
if __name__ == "__main__":
    print("🚀 http://127.0.0.1:5000")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)


