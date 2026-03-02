import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class SubtitleStabilizer:
    def __init__(self, threshold=0.7):
        self.last_subtitle = ""
        self.threshold = threshold

    def stabilize(self, new_subtitle: str):
        """
        Stabilizes subtitles by comparing with the previous one.
        If similar, it returns the previous one to avoid flickering, 
        or a merged version if it's an extension.
        """
        if not self.last_subtitle:
            self.last_subtitle = new_subtitle
            return new_subtitle

        # Compare similarity
        similarity = SequenceMatcher(None, self.last_subtitle, new_subtitle).ratio()
        
        if similarity > self.threshold:
            # If very similar, stick with the new one as it might be a correction
            self.last_subtitle = new_subtitle
            return new_subtitle
        else:
            # Check if it's a completely new sentence (low similarity)
            self.last_subtitle = new_subtitle
            return new_subtitle

    def clear(self):
        self.last_subtitle = ""
