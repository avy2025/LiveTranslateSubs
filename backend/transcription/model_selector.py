from utils.hardware_detection import detect_hardware
import logging

logger = logging.getLogger(__name__)

def get_model_config():
    """
    Selects Whisper model and compute type based on hardware availability.
    """
    hw = detect_hardware()
    
    # Defaults (Low-end)
    model_name = "tiny"
    device = "cpu"
    compute_type = "int8"
    
    if hw["cuda_available"]:
        # High-end (GPU detected)
        model_name = "small" # User recommended small or medium for high-end
        if hw["gpu_memory_gb"] > 4:
            model_name = "medium"
        device = "cuda"
        compute_type = "float16"
    elif hw["ram_gb"] > 7:
        # Mid-range (8GB+ RAM, no GPU)
        model_name = "base"
        device = "cpu"
        compute_type = "int8"
        
    logger.info(f"Adaptive Selection: Model={model_name}, Device={device}, Compute={compute_type}")
    
    return {
        "model_name": model_name,
        "device": device,
        "compute_type": compute_type
    }
