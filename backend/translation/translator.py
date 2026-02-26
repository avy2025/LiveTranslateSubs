from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class Translator:
    def __init__(self, model_name="Helsinki-NLP/opus-mt-hi-en"):
        logger.info(f"Initializing Professional Translator with {model_name}...")
        try:
            self.translator = pipeline("translation", model=model_name)
            logger.info("Professional Translator ready.")
        except Exception as e:
            logger.error(f"Failed to initialize Translator: {e}")
            self.translator = None

    def translate(self, text):
        if not text or not self.translator:
            return text
        
        try:
            # Clean text
            text = text.strip()
            if not text:
                return ""
                
            result = self.translator(text, max_length=512)
            if result and len(result) > 0:
                return result[0]['translation_text']
        except Exception as e:
            logger.error(f"Translation error: {e}")
        
        return text

translator_instance = None

def get_translator():
    global translator_instance
    if translator_instance is None:
        translator_instance = Translator()
    return translator_instance
