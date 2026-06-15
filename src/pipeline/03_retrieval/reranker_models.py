from __future__ import annotations

import gc
import os
from functools import lru_cache

from sentence_transformers import CrossEncoder

from src.utils.model_device import describe_model_device, get_model_device

DEFAULT_RERANKER_MODEL = "zeroentropy/zerank-2-reranker"


def _downloads_disabled() -> bool:
    return os.environ.get("HF_HUB_OFFLINE", "").strip().lower() in {"1", "true", "yes"}


def _trust_remote_code_enabled() -> bool:
    return os.environ.get("RERANKER_TRUST_REMOTE_CODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


def reranker_enabled() -> bool:
    return os.environ.get("RERANKER_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def selected_reranker_model() -> str:
    return os.environ.get("RERANKER_MODEL", DEFAULT_RERANKER_MODEL).strip()


def describe_reranker_runtime(model_id: str | None = None) -> str:
    device = get_model_device()
    download_mode = "cached only" if _downloads_disabled() else "downloads allowed"
    trust_remote = ", trust_remote_code" if _trust_remote_code_enabled() else ""
    model_note = f" for {model_id}" if model_id else ""
    return f"CrossEncoder on {describe_model_device(device)} ({download_mode}{trust_remote}){model_note}"


@lru_cache(maxsize=2)
def _load_reranker_model_cached(
    model_id: str,
    device: str,
    local_files_only: bool,
    trust_remote_code: bool,
) -> CrossEncoder:
    return CrossEncoder(
        model_id,
        device=device,
        local_files_only=local_files_only,
        trust_remote_code=trust_remote_code,
    )


def load_reranker_model(model_id: str | None = None, allow_download: bool = True) -> CrossEncoder:
    model_id = (model_id or selected_reranker_model()).strip()
    if not model_id:
        raise ValueError("Reranker model id is required.")

    local_files_only = not allow_download or _downloads_disabled()
    return _load_reranker_model_cached(
        model_id,
        get_model_device(),
        local_files_only,
        _trust_remote_code_enabled(),
    )


def unload_reranker_models() -> None:
    """Release cached cross-encoders and unused accelerator memory."""
    _load_reranker_model_cached.cache_clear()
    gc.collect()

    try:
        import torch
    except ImportError:
        return

    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
