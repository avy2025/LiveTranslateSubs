import numpy as np
import librosa
from backend import config
import logging

logger = logging.getLogger(__name__)

class AudioBuffer:
    def __init__(self):
        self.buffer = np.zeros(0, dtype=np.float32)
        self.sample_rate = config.SAMPLE_RATE

    def add_chunk(self, chunk: np.ndarray):
        """
        Adds an audio chunk to the buffer.
        Ensures 16kHz mono float32 format.
        """
        try:
            # Ensure float32
            audio = chunk.astype(np.float32)
            
            # Convert Stereo to Mono
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=0)

            # Resample to 16kHz (Standardizing input SR to 48kHz for resampling)
            audio_16k = librosa.resample(
                audio, 
                orig_sr=48000, 
                target_sr=self.sample_rate
            )
            
            # Normalize amplitude
            if np.abs(audio_16k).max() > 0:
                audio_16k = audio_16k / np.abs(audio_16k).max()
            
            self.buffer = np.concatenate([self.buffer, audio_16k])
            
            # Keep buffer within limits
            max_samples = int(config.MAX_BUFFER_SECONDS * self.sample_rate)
            if len(self.buffer) > max_samples:
                self.buffer = self.buffer[-max_samples:]
        except Exception as e:
            logger.error(f"Error in AudioBuffer.add_chunk: {e}")

    def get_window(self, start_seconds: float, duration_seconds: float):
        """
        Retrieves a window of audio from the buffer.
        """
        start_sample = int(start_seconds * self.sample_rate)
        end_sample = int((start_seconds + duration_seconds) * self.sample_rate)
        
        if start_sample < 0: start_sample = 0
        
        # If requested window is beyond current buffer, return what we have
        actual_end = min(end_sample, len(self.buffer))
        
        if start_sample >= actual_end:
            return np.zeros(0, dtype=np.float32)
            
        return self.buffer[start_sample:actual_end]

    def get_total_duration(self):
        return len(self.buffer) / self.sample_rate

    def clear(self):
        self.buffer = np.zeros(0, dtype=np.float32)
