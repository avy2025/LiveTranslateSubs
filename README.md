# 🎤 LiveTranslateSubs — High-Performance Live Speech Translation

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688?style=for-the-badge&logo=fastapi)
![Whisper](https://img.shields.io/badge/Whisper-faster--whisper-orange?style=for-the-badge)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-black?style=for-the-badge&logo=socketdotio)

**LiveTranslateSubs** is a sophisticated, real-time speech translation system that captures live microphone audio from the browser, translates it into English, and displays it with ultra-low latency. 

Recently overhauled to use a modern **FastAPI + Asyncio** architecture, it now supports true **word-level streaming** and professional-grade features for streamers and users alike.

---

## ✨ New & Updated Features

- 🏎️ **FastAPI & Asyncio Backend**
  - Fully asynchronous architecture for high concurrency and lower latency.
  - Replaced legacy Flask/Eventlet with modern, scalable `FastAPI` and `python-socketio`.

- 🌊 **True Word-Level Streaming**
  - Captions appear word-by-word as you speak, providing a "truly live" feel.
  - Uses Whisper's word-level timestamps for granular emission.

- 🧠 **Dynamic Model & GPU Control**
  - **Model Selection**: Switch between `Tiny`, `Base`, `Small`, `Medium`, and `Large-v3` on the fly.
  - **Hardware Toggle**: Seamlessly switch between CPU and GPU (NVIDIA CUDA) acceleration from the UI.

- 🗣️ **Manual Language Lock**
  - Added a language selector to prevent auto-detection errors.
  - Significantly improves translation quality and accuracy by providing context.

- 🎥 **OBS Overlay Mode**
  - Dedicated transparent view at `/overlay` for live streamers.
  - Optimized font styling for high visibility on video.

- 💾 **Subtitle Export**
  - Save your live sessions as professional `.srt` or `.vtt` files directly from the browser.

---

## 🛠 Tech Stack

### Backend
- **FastAPI**: Asynchronous web framework.
- **Python-SocketIO**: Real-time bidirectional communication.
- **faster-whisper**: High-performance Whisper implementation via CTranslate2.
- **NumPy**: Efficient audio buffer processing.

### Frontend
- **Modern UI**: Dark-mode interface with smooth transitions.
- **AudioWorklet**: Low-latency, high-quality audio capture with linear interpolation resampling.
- **Web Audio API**: Real-time microphone capture.

---

## ⚙️ Installation & Setup

1️⃣ **Clone the Repository**
```bash
git clone https://github.com/your-username/LiveTranslateSubs.git
cd LiveTranslateSubs
```

2️⃣ **Install Dependencies**
```bash
pip install -r requirements.txt
```

3️⃣ **Run the Application**
```bash
python app.py
```

4️⃣ **Open in Browser**
Access the main interface at: `http://127.0.0.1:5000`
Access the OBS Overlay at: `http://127.0.0.1:5000/overlay`

---

## 👤 Author
**Ranjan Thakur**
Engineering Student | GenAI & Real-Time Systems Enthusiast

---

## ⭐ Final Note
This project demonstrates how to build robust, production-quality live transcription systems by combining modern web technologies with state-of-the-art AI models.

Feel free to fork, improve, and experiment 🚀