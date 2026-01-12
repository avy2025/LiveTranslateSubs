Markdown

# 🎤 LiveTranslateSubs — Real-Time Speech Translation

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-green?style=for-the-badge&logo=flask)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange?style=for-the-badge)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-black?style=for-the-badge&logo=socketdotio)

LiveTranslateSubs is a high-performance, real-time speech-to-translation web application. It streams raw audio from your browser and uses **OpenAI Whisper (via faster-whisper)** to translate multilingual speech into English text with minimal latency.

---

## ✨ Features
- 🎙️ **Direct PCM Streaming:** Uses Web Audio API to stream raw `float32` chunks (No FFmpeg overhead).
- 🧠 **Instant Translation:** Specifically tuned for `Multilingual → English` translation tasks.
- ⚡ **Optimized Inference:** Powered by `faster-whisper` with `int8` quantization for smooth CPU performance.
- 🔊 **VAD Filtering:** Built-in Voice Activity Detection to filter out background silence.
- 🌑 **Modern UI:** Clean, dark-themed interface for live captioning.

---

## 🧠 Technical Workflow

The application has been upgraded to handle audio more efficiently than traditional blob-based recording:



1.  **Frontend:** Captures raw mono audio at **16,000Hz** using `ScriptProcessorNode`.
2.  **Transport:** Emits Base64 encoded PCM data over **WebSockets** every 4096 samples.
3.  **Backend:** Buffers chunks until a **2.0-second** window is met to ensure context for the AI.
4.  **AI Engine:** Whisper processes the buffer in a background thread to prevent UI freezing.
5.  **Delivery:** The translated English text is pushed back to the UI in real-time.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Flask-SocketIO
- **AI Model:** `faster-whisper` (Tiny model)
- **Frontend:** JavaScript (Web Audio API), Socket.io-client
- **Processing:** NumPy

---

## ⚙️ Installation & Setup

### 1. Clone the repository
```bash
git clone [https://github.com/your-username/LiveTranslateSubs.git](https://github.com/your-username/LiveTranslateSubs.git)
cd LiveTranslateSubs
2. Install Dependencies
Bash

pip install flask flask-socketio faster-whisper numpy
3. Run the Application
Bash

python app.py
4. Open the Interface
Navigate to http://127.0.0.1:5000, click Start, and begin speaking.

📁 Project Structure
Plaintext

.
├── app.py              # Flask Server + WebSocket Logic + AI Inference
├── README.md           # Documentation
└── requirements.txt    # Project dependencies
📌 Changes Made in this Version
✅ Removed FFmpeg Dependency: Now streams raw PCM directly from the browser.

✅ Added Thread Locking: buffer_lock implemented to prevent memory corruption during high-frequency audio streaming.

✅ Optimized Sampling: Forced 16kHz sample rate on both ends for perfect Whisper compatibility.

✅ Automatic Translation: Hardcoded task="translate" for immediate English output.

🔮 Future Roadmap
[ ] Add support for original transcript + translation side-by-side.

[ ] Implement a visual volume meter (Gain Node).

[ ] Support for selecting larger models (Base/Small/Medium) via the UI.

Author: Ranjan Thakur
