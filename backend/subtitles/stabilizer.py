import logging

logger = logging.getLogger(__name__)

class SubtitleStabilizer:
    def __init__(self):
        self.last_subtitle = ""
        self.history = []
        self.max_history = 5

    def stabilize(self, new_text):
        """
        Reduces flickering and prevents repeated outputs.
        """
        if not new_text or new_text.strip() == "":
            return self.last_subtitle

        # Basic stabilization: if identical to last, ignore
        if new_text.strip() == self.last_subtitle.strip():
            return self.last_subtitle

        # Avoid repeating identical subtitles from history
        if new_text.strip() in self.history:
            return self.last_subtitle

        self.last_subtitle = new_text.strip()
        self.history.append(self.last_subtitle)
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        return self.last_subtitle

    def is_sentence_complete(self, text):
        """
        Check if the text likely ends a sentence.
        """
        if not text:
            return False
        # Improved sentence end detection including Hindi punctuation
        return text.strip().endswith(('.', '?', '!', '।'))

    def clear(self):
        self.last_subtitle = ""
        self.history = []

stabilizer_instance = None

def get_stabilizer():
    global stabilizer_instance
    if stabilizer_instance is None:
        stabilizer_instance = SubtitleStabilizer()
    return stabilizer_instance
