from __future__ import annotations

import os
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.core.model_device import describe_model_device, get_model_device

DEFAULT_EMBEDDING_MODEL = "Octen/Octen-Embedding-0.6B"

AVAILABLE_EMBEDDING_MODELS = (
    "Octen/Octen-Embedding-0.6B",
    "Octen/Octen-Embedding-4B",
    "Octen/Octen-Embedding-8B",
    "BAAI/bge-m3",
)


def _trust_remote_code_enabled() -> bool:
    return os.environ.get("EMBEDDING_TRUST_REMOTE_CODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def describe_embedding_runtime(model_id: str | None = None) -> str:
    device = get_model_device()
    download_mode = "cached only" if _downloads_disabled() else "downloads allowed"
    trust_remote = ", trust_remote_code" if _trust_remote_code_enabled() else ""
    model_note = f" for {model_id}" if model_id else ""
    return f"SentenceTransformer on {describe_model_device(device)} ({download_mode}{trust_remote}){model_note}"


def _downloads_disabled() -> bool:
    return os.environ.get("HF_HUB_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


@lru_cache(maxsize=8)
def _load_embedding_model_cached(
    model_id: str,
    device: str,
    local_files_only: bool,
    trust_remote_code: bool,
) -> SentenceTransformer:
    return SentenceTransformer(
        model_id,
        device=device,
        local_files_only=local_files_only,
        trust_remote_code=trust_remote_code,
    )


def load_embedding_model(model_id: str, allow_download: bool = True) -> SentenceTransformer:
    """
    Load a SentenceTransformer embedding model on the preferred local device.

    When allow_download is false, Hugging Face is restricted to locally cached
    files. This lets the vector builder validate model availability before it
    recreates the Chroma collection.
    """
    if not model_id or not str(model_id).strip():
        raise ValueError("Embedding model id is required.")

    local_files_only = not allow_download or _downloads_disabled()
    return _load_embedding_model_cached(
        str(model_id).strip(),
        get_model_device(),
        local_files_only,
        _trust_remote_code_enabled(),
    )
