# ================== FORCE FFMPEG (IMPORTANT) ==================
import os
os.environ["PATH"] += os.pathsep + r"C:\Users\admin\Downloads\ffmpeg\bin"

# ================== IMPORTS ==================
from flask import Flask
from flask_socketio import SocketIO, emit
from faster_whisper import WhisperModel
import base64
import numpy as np
import ffmpeg
import shutil

# ================== DEBUG CHECK ==================
print("FFmpeg found at:", shutil.which("ffmpeg"))

# ================== FLASK APP ==================
app = Flask(__name__)
app.config["SECRET_KEY"] = "live-translate"
socketio = SocketIO(app, cors_allowed_origins="*")

# ================== LOAD WHISPER ==================
print("🔄 Loading Whisper model...")
model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)
print("✅ Whisper ready!")

# ================== AUDIO DECODER ==================
def decode_webm_opus(audio_bytes):
    """
    Converts WebM/Opus bytes to PCM float32 @16kHz
    """
    out, err = (
        ffmpeg
        .input("pipe:0")
        .output(
            "pipe:1",
            format="f32le",
            ac=1,
            ar="16000"
        )
        .run(
            input=audio_bytes,
            capture_stdout=True,
            capture_stderr=True
        )
    )
    return np.frombuffer(out, np.float32)

# ================== ROUTE ==================
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>LiveTranslateSubs</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <style>
        body { font-family: Arial; background: #111; color: white; text-align: center; }
        button { padding: 15px 30px; font-size: 18px; border-radius: 20px; border: none; }
        .recording { background: red; color: white; }
        #subs { margin-top: 20px; background: black; color: #0f0; padding: 20px; height: 300px; overflow-y: auto; font-size: 22px; }
    </style>
</head>
<body>
    <h1>🎤 Live Whisper Translation</h1>
    <button id="btn">Record 4s</button>
    <p id="status">Speak clearly & loudly</p>
    <div id="subs">Waiting...</div>

<script>
const socket = io();
let recorder, stream, chunks = [];

document.getElementById("btn").onclick = async () => {
    chunks = [];
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    recorder = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
    recorder.ondataavailable = e => chunks.push(e.data);
    recorder.onstop = sendAudio;

    recorder.start();
    document.getElementById("btn").className = "recording";
    document.getElementById("btn").innerText = "Recording...";
    document.getElementById("status").innerText = "Recording... Speak now!";

    setTimeout(() => {
        recorder.stop();
        stream.getTracks().forEach(t => t.stop());
    }, 4000);
};

async function sendAudio() {
    const blob = new Blob(chunks, { type: "audio/webm;codecs=opus" });
    const buffer = await blob.arrayBuffer();
    const bytes = new Uint8Array(buffer);

    let binary = "";
    for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
    }

    const base64Audio = btoa(binary);

    socket.emit("audio_chunk", {
        audio: base64Audio,
        size: blob.size
    });

    document.getElementById("btn").className = "";
    document.getElementById("btn").innerText = "Record again";
}

socket.on("subtitle", data => {
    document.getElementById("subs").innerHTML += "<p>" + data.text + "</p>";
    document.getElementById("subs").scrollTop = document.getElementById("subs").scrollHeight;
    document.getElementById("status").innerText = "Done";
});
</script>
</body>
</html>
"""

# ================== SOCKET HANDLER ==================
@socketio.on("audio_chunk")
def handle_audio(data):
    try:
        audio_bytes = base64.b64decode(data["audio"])
        print("📡 Received bytes:", len(audio_bytes))

        if len(audio_bytes) < 3000:
            emit("subtitle", {
                "text": "Speak louder or longer",
                "lang": "en"
            })
            return

        audio = decode_webm_opus(audio_bytes)
        print("🎧 Audio samples:", audio.shape)

        segments, info = model.transcribe(
            audio,
            task="translate",
            vad_filter=True,
            beam_size=5
        )

        text = " ".join(
            s.text.strip()
            for s in segments
            if s.text.strip()
        )

        emit("subtitle", {
            "text": text if text else "[No speech detected]",
            "lang": info.language or "unknown"
        })

        print("📝 Result:", text)

    except Exception as e:
        print("❌ Error:", e)
        emit("subtitle", {
            "text": "Error processing audio",
            "lang": "en"
        })

# ================== RUN ==================
if __name__ == "__main__":
    print("🚀 Server running at http://127.0.0.1:5000")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)

