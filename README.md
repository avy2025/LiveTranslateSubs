![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-Web_Framework-green)
![Whisper](https://img.shields.io/badge/Whisper-GenAI-orange)
![Socket.IO](https://img.shields.io/badge/Socket.IO-Realtime-black)
![Status](https://img.shields.io/badge/Status-Working-success)

# 🎤 LiveTranslateSubs — Real-Time Speech Translation

LiveTranslateSubs is a **real-time speech-to-text and translation web application** built using **Flask, Socket.IO, and OpenAI Whisper (faster-whisper)**.  
It captures microphone audio from the browser, transcribes spoken language, and translates it into English with **low latency**.

This project demonstrates practical usage of **GenAI, audio processing, WebSockets, and full-stack development**.

---

## 🚀 Features

- 🎙️ Live microphone audio recording from browser  
- 🧠 Speech recognition using **Whisper (faster-whisper)**  
- 🌍 Automatic language detection & translation  
- ⚡ Real-time communication via **Socket.IO**  
- 🔊 Voice Activity Detection (VAD) for better accuracy  
- 💻 Optimized for **CPU execution** (no GPU required)

---

## 🛠️ Tech Stack

**Frontend**
- HTML, CSS, JavaScript
- MediaRecorder API
- Socket.IO Client

**Backend**
- Python
- Flask
- Flask-SocketIO
- faster-whisper
- FFmpeg
- NumPy

---
## 🧠 How It Works

1. Browser records microphone audio using MediaRecorder API
2. Audio is sent to the backend via Socket.IO
3. FFmpeg converts WebM/Opus audio to PCM float32
4. Whisper model performs speech recognition
5. Detected speech is translated into English
6. Transcribed subtitles are sent back to the browser in real time
---
## 📁 Project Structure

LiveTranslationCaption/
│
├── app.py # Main Flask + Socket.IO server
├── README.md # Project documentation
└── requirements.txt # Python dependencies

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/LiveTranslateSubs.git
cd LiveTranslateSubs

2️⃣ Install Python dependencies
pip install flask flask-socketio faster-whisper ffmpeg-python numpy

3️⃣ Install FFmpeg (Required)

Download from: https://www.gyan.dev/ffmpeg/builds/

Extract and note the bin path

Example:

C:\Users\admin\Downloads\ffmpeg\bin


FFmpeg is required for decoding audio.
▶️ Run the Application
python app.py


Open your browser and visit:

http://127.0.0.1:5000


Click Record, speak clearly, and see live translated subtitles

📌 Key Learnings

Real-time audio streaming using WebSockets

Audio format conversion (WebM → PCM)

Integrating GenAI models in web applications

Handling browser microphone APIs

Building production-ready Flask applications

🔮 Future Improvements

True real-time streaming (chunk-based transcription)

Support for original + translated subtitles

Improved accuracy using larger Whisper models

Deployment on cloud (Render / Railway)

Mobile-friendly UI

🤝 Contributing

Contributions are welcome!
Feel free to fork this repo, raise issues, or submit pull requests.

📜 License

This project is licensed under the MIT License.

👨‍💻 Author

Ranjan Thakur
