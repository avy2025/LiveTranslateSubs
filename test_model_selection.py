import sys
import os
from unittest.mock import patch

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.transcription.model_selector import get_model_config

def test_model_selection():
    print("Testing Model Selection Logic...")
    
    # 1. Test Baseline (No GPU, 8GB RAM)
    with patch('backend.transcription.model_selector.detect_hardware') as mock_hw:
        mock_hw.return_value = {
            "ram_gb": 8.0,
            "cuda_available": False,
            "gpu_name": None,
            "gpu_memory_gb": 0
        }
        config = get_model_config()
        print(f"Scenario: 8GB RAM, CPU-only -> Expected: base, Got: {config['model_name']}")
        assert config['model_name'] == "base"

    # 2. Test Low-End Fallback (No GPU, 2GB RAM)
    with patch('backend.transcription.model_selector.detect_hardware') as mock_hw:
        mock_hw.return_value = {
            "ram_gb": 2.0,
            "cuda_available": False,
            "gpu_name": None,
            "gpu_memory_gb": 0
        }
        config = get_model_config()
        print(f"Scenario: 2GB RAM, CPU-only -> Expected: tiny, Got: {config['model_name']}")
        assert config['model_name'] == "tiny"

    # 3. Test High-End (GPU available)
    with patch('backend.transcription.model_selector.detect_hardware') as mock_hw:
        mock_hw.return_value = {
            "ram_gb": 16.0,
            "cuda_available": True,
            "gpu_name": "RTX 3080",
            "gpu_memory_gb": 10.0
        }
        config = get_model_config()
        print(f"Scenario: GPU (10GB VRAM) -> Expected: medium, Got: {config['model_name']}")
        assert config['model_name'] == "medium"

    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_model_selection()
