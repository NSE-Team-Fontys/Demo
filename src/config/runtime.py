from pathlib import Path
import os

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except ImportError:
    pass

# Fix for macOS Apple Silicon deadlocks when using HuggingFace models in Flask.
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Let unsupported PyTorch MPS ops fall back to CPU instead of failing requests.
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
