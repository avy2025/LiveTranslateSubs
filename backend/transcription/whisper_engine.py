from faster_whisper import WhisperModel
from backend.transcription.model_selector import get_model_config
from backend import config
import logging
import numpy as np

logger = logging.getLogger(__name__)

class WhisperEngine:
    def __init__(self):
        conf = get_model_config()
        self.model_name = conf["model_name"]
        self.device = conf["device"]
        self.compute_type = conf["compute_type"]
        
        logger.info(f"Initializing WhisperEngine with {self.model_name} on {self.device}...")
        self.model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type
        )
        logger.info("WhisperEngine ready.")

    def transcribe(self, audio_data: np.ndarray):
        """
        Transcribes audio data (Hindi) with safety guards.
        Strictly use transcribe task.
        """
        # 1. Silence Guard
        if len(audio_data) == 0:
            return [], None
            
        mean_abs = np.abs(audio_data).mean()
        if mean_abs < 0.01:
            logger.info(f"Skipping transcription: Silence detected (mean_abs={mean_abs:.4f})")
            return [], None

        # 2. Minimum Duration Guard
        if len(audio_data) < 16000: # Less than 1 second (at 16kHz)
            logger.info(f"Skipping transcription: Audio too short ({len(audio_data)} samples)")
            return [], None

        # 3. Transcribe
        segments, info = self.model.transcribe(
            audio_data,
            language=config.WHISPER_LANGUAGE,
            task=config.WHISPER_TASK,
            beam_size=config.BEAN_SIZE,
            best_of=config.BEST_OF,
            temperature=config.TEMPERATURE,
            condition_on_previous_text=config.CONDITION_ON_PREVIOUS_TEXT,
            no_repeat_ngram_size=config.NO_REPEAT_NGRAM_SIZE,
            vad_filter=config.VAD_FILTER
        )
        
        return list(segments), info

whisper_engine = None

def get_whisper_engine():
    global whisper_engine
    if whisper_engine is None:
        whisper_engine = WhisperEngine()
    return whisper_engine
