import logging

logger = logging.getLogger(__name__)

class SentenceBuffer:
    def __init__(self):
        self.current_sentence = ""

    def add_text(self, text: str):
        """
        Adds transcribed text and checks for sentence completion.
        """
        self.current_sentence += " " + text
        self.current_sentence = self.current_sentence.strip()
        
        # Check for punctuation markers that indicate end of sentence
        if any(self.current_sentence.endswith(p) for p in [".", "?", "!", "।"]):
            sentence = self.current_sentence
            self.current_sentence = ""
            return sentence
        
        return None

    def flush(self):
        """
        Returns the current accumulated text and clears it.
        """
        sentence = self.current_sentence
        self.current_sentence = ""
        return sentence
