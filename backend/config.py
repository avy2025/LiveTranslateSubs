import logging
import os
from pathlib import Path

# Base Directory (Project Root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging
LOG_LEVEL = logging.INFO

# Audio Configuration
SAMPLE_RATE = 16000
WINDOW_SIZE = 4.0      # 4 seconds window
WINDOW_STRIDE = 2.0    # 2 seconds overlap
MAX_BUFFER_SECONDS = 60.0

# Transcription Parameters
BEAN_SIZE = 3
BEST_OF = 3
TEMPERATURE = 0.0
VAD_FILTER = True
CONDITION_ON_PREVIOUS_TEXT = False
NO_REPEAT_NGRAM_SIZE = 3
WHISPER_TASK = "transcribe"
WHISPER_LANGUAGE = "hi"

# Subtitle Stabilization
STABILIZATION_THRESHOLD = 0.8  # Jaccard similarity or similar metric

# Server Configuration
HOST = "127.0.0.1"
PORT = 5000

# Directory Paths
STATIC_DIR = str(BASE_DIR / "frontend")
TEMPLATES_DIR = str(BASE_DIR / "frontend")
