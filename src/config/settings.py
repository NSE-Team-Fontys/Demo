import os

DEFAULT_LLM_PROVIDER = os.environ.get("DEFAULT_LLM_PROVIDER", "llama.cpp")
DEFAULT_LLM_MODEL = os.environ.get(
    "DEFAULT_LLM_MODEL",
    "unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL",
)
LLAMA_CPP_BASE_URL = os.environ.get("LLAMA_CPP_BASE_URL", "http://127.0.0.1:8080")
LLAMA_CPP_API_KEY = os.environ.get("LLAMA_CPP_API_KEY", "no-key")
LLAMA_CPP_MAX_TOKENS = int(os.environ.get("LLAMA_CPP_MAX_TOKENS", "4096"))
LLAMA_CPP_SERVER_BIN = os.environ.get("LLAMA_CPP_SERVER_BIN", "llama-server")
LLAMA_CPP_STARTUP_TIMEOUT = int(os.environ.get("LLAMA_CPP_STARTUP_TIMEOUT", "180"))

RERANKER_CANDIDATE_MULTIPLIER = int(
    os.environ.get("RERANKER_CANDIDATE_MULTIPLIER", "5")
)
RERANKER_MAX_CANDIDATES = int(os.environ.get("RERANKER_MAX_CANDIDATES", "100"))
LLM_CONTEXT_DOCUMENTS = int(os.environ.get("LLM_CONTEXT_DOCUMENTS", "100"))
INSIGHT_CACHE_VERSION = 4
