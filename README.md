# 🎤 LiveTranslateSubs — Near Real-Time Speech Translation

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-green?style=for-the-badge&logo=flask)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange?style=for-the-badge)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-black?style=for-the-badge&logo=socketdotio)

**LiveTranslateSubs** is a near real-time, browser-based speech translation system that captures live microphone audio, streams it to a Python backend, and translates **any spoken language into English subtitles** using **Whisper via faster-whisper**.

The project focuses on **low latency, correctness, and architectural clarity**, avoiding unreliable delta-text hacks and deprecated browser APIs.

---

## ✨ Key Features

- 🎙 **True Live Audio Streaming**
  - Streams raw `float32` PCM audio from the browser
  - No FFmpeg, no file uploads, no blobs

- 🔁 **Sliding Window Transcription**
  - Rolling audio window with overlap
  - Prevents context loss and repeated hallucinations

- 🧠 **Robust Deduplication**
  - Uses **absolute timestamps + text hashing**
  - Avoids duplicate subtitles without fragile string comparisons

- ⚡ **Optimized Whisper Inference**
  - Powered by `faster-whisper`
  - CPU-friendly `int8` quantization

- 🗣 **Automatic Multilingual → English Translation**
  - Uses Whisper’s built-in translation mode
  - No language selection required

- ⏯ **Start / Pause Control**
  - Toggle live transcription without refreshing the page

- 🌑 **Clean Dark UI**
  - Minimal, distraction-free subtitle display

---

## 🧠 Architecture Overview

Unlike naïve implementations, LiveTranslateSubs avoids common pitfalls like timestamp resets, buffer discontinuity, and broken delta detection.

### High-Level Flow

1. **Browser**
   - Captures microphone audio using **AudioWorklet**
   - Resamples audio from device rate (usually 48kHz) → **16kHz**
   - Sends small PCM chunks via Socket.IO

2. **Backend**
   - Appends audio to a rolling window buffer
   - Tracks absolute audio time cursor
   - Decodes every ~1.8 seconds

3. **Whisper Engine**
   - Transcribes the **entire sliding window**
   - Uses VAD to ignore silence
   - Produces stable segment timestamps

4. **Deduplication**
   - Each segment mapped to absolute time
   - Previously emitted segments are skipped safely

5. **Frontend**
   - Receives translated subtitles in near real-time
   - Appends text smoothly without flicker

---

## 🛠 Tech Stack

### Backend
- Python 3.10+
- Flask
- Flask-SocketIO
- faster-whisper
- NumPy
- Eventlet (see limitations)

### Frontend
- HTML / CSS
- JavaScript
- Web Audio API
- AudioWorklet
- Socket.IO Client

---

## 📁 Project Structure

```text
.
├── app.py
├── static/
│   └── audio-worklet.js
├── templates/
│   └── index.html
├── README.md
└── requirements.txt
⚙️ Installation & Setup
1️⃣ Clone the Repository
bash
Copy code
git clone https://github.com/your-username/LiveTranslateSubs.git
cd LiveTranslateSubs
2️⃣ Install Dependencies
bash
Copy code
pip install flask flask-socketio faster-whisper numpy eventlet
⚠️ Note: faster-whisper requires ctranslate2.
On Windows, use CPU unless CUDA is properly installed.

3️⃣ Run the Application
bash
Copy code
python app.py
4️⃣ Open in Browser
cpp
Copy code
http://127.0.0.1:5000
Click Start, speak in any language, and see English subtitles appear.

🚧 Limitations (Important)
This project is near real-time, not true streaming ASR. Current limitations include:

❌ Not word-by-word streaming

Whisper is segment-based, not token-streaming

❌ Eventlet is deprecated

Used for stability with Flask-SocketIO

Migration to asyncio or Quart is recommended

❌ Latency depends on CPU

Lower-end CPUs may see 2–3s delay

GPU improves latency significantly

❌ No speaker diarization

Multiple speakers are not separated

❌ No punctuation stabilization

Early segments may slightly change as context improves

🔮 Improvements Still Needed
Planned and recommended enhancements:

 Migrate from Eventlet → asyncio-based backend

 True token-level streaming (Whisper.cpp / Realtime models)

 Display timestamps or sentence-by-sentence captions

 Export subtitles as .srt / .vtt

 Add language auto-detection display

 Model selector (Tiny / Base / Small / Medium)

 GPU acceleration toggle

 Noise suppression & gain control

 OBS / live streaming overlay mode

👤 Author
Ranjan Thakur
Engineering Student | GenAI & Real-Time Systems Enthusiast

⭐ Final Note
This project prioritizes correct real-time behavior over shortcuts.
If you’re building live transcription systems, this repo demonstrates how to do it the right way.

Feel free to fork, improve, and experiment 🚀