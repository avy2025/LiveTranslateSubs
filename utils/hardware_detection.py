import psutil
import torch
import logging

logger = logging.getLogger(__name__)

def detect_hardware():
    """
    Detects available RAM and NVIDIA GPU (CUDA) availability.
    Returns a dictionary with hardware specs.
    """
    # Get total RAM in GB
    total_ram = psutil.virtual_memory().total / (1024 ** 3)
    
    # Check for CUDA availability
    cuda_available = torch.cuda.is_available()
    gpu_name = None
    gpu_memory = 0
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        # Get free/total memory in GB
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    
    hardware_info = {
        "ram_gb": total_ram,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "gpu_memory_gb": gpu_memory
    }
    
    logger.info(f"Hardware Detected: RAM={total_ram:.2f}GB, CUDA={cuda_available}, GPU={gpu_name}, GPU_RAM={gpu_memory:.2f}GB")
    return hardware_info

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(detect_hardware())
