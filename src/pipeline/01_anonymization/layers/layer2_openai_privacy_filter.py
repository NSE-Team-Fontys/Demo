from __future__ import annotations

import logging
import os
from typing import Optional

import torch
from transformers import pipeline as hf_pipeline

from src.utils.model_device import get_model_device, get_pipeline_device

from .layer2_text_norm import normalize_for_ner
from .layer_utils import Span

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_torch_device = get_model_device()
_device = get_pipeline_device(_torch_device)
_use_fp16 = os.environ.get("LAYER2_FP16", "").lower() in {"1", "true", "yes"}

# Optional model: only works if available in your environment.
_MODEL_ID = "openai/privacy-filter"

try:
    kwargs = {
        "task": "token-classification",
        "model": _MODEL_ID,
        "aggregation_strategy": "simple",
        "device": _device,
    }
    if _torch_device != "cpu" and _use_fp16:
        kwargs["model_kwargs"] = {"torch_dtype": torch.float16}
    _ner = hf_pipeline(**kwargs)
    _load_error = None
except Exception as e:
    _ner = None
    _load_error = e
    logger.warning(f"{_MODEL_ID} failed to load: {e}. Layer will be skipped.")


def unload_models() -> None:
    global _ner
    _ner = None
    import gc
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()


def ensure_openai_privacy_filter_available() -> None:
    """Raise a clear error if the selected OpenAI Privacy Filter layer is unavailable."""
    if _ner is None:
        detail = f" ({_load_error})" if _load_error else ""
        raise RuntimeError(
            f"{_MODEL_ID} is selected but the model could not be loaded. "
            "Remove this experimental layer or update/install a Transformers version that supports it."
            + detail
        )


def _strip_prefix(label: str) -> str:
    s = (label or "").strip()
    for prefix in ("B-", "I-", "E-", "S-", "O-"):
        if len(s) > len(prefix) and s.startswith(prefix):
            return s[len(prefix) :]
    return s


def _tag(group: str) -> str:
    label = _strip_prefix(str(group or "")).lower()
    if label == "private_person":
        return "[NAME]"
    if label == "private_address":
        return "[LOCATION]"
    if any(k in label for k in ("health", "medical", "condition", "diagnosis", "illness", "disease", "disability", "medication")):
        return "[HEALTH]"
    return "[PII]"


def _config_allows(config: Optional[dict], tag: str) -> bool:
    if not config:
        return True
    if tag == "[NAME]":
        return bool(config.get("names", True))
    if tag == "[LOCATION]":
        return bool(config.get("locations", True))
    if tag == "[PII]":
        return bool(config.get("pii", True))
    if tag == "[HEALTH]":
        return bool(config.get("pii", True))
    return True


def _spans_tuple_for_text(text: str, entities: list, config: Optional[dict]) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for ent in sorted(entities, key=lambda e: e["end"] - e["start"], reverse=True):
        span_text = text[ent["start"] : ent["end"]]
        if not span_text.strip() or len(span_text) < 2:
            continue
        tag = _tag(ent.get("entity_group", ""))
        if not _config_allows(config, tag):
            continue
        spans.append((ent["start"], ent["end"], tag))
    return spans


def openai_privacy_filter_collect_batch(texts: list, config: Optional[dict] = None) -> list:
    """Batch collect (start, end, tag) per text — same shape as eu_pii_collect_batch."""
    ensure_openai_privacy_filter_available()
    if not texts:
        return [[] for _ in texts]
    try:
        texts_for_ner = [normalize_for_ner(t) if isinstance(t, str) else "" for t in texts]
        batch_entities = _ner(texts_for_ner, batch_size=len(texts_for_ner))
    except Exception as e:
        logger.warning("%s collect batch error: %s", _MODEL_ID, e)
        return [[] for _ in texts]

    return [_spans_tuple_for_text(t, ent, config) for t, ent in zip(texts, batch_entities)]


def openai_privacy_filter_collect_spans(text: str, config: Optional[dict] = None) -> list[Span]:
    ensure_openai_privacy_filter_available()
    if not text or not text.strip():
        return []
    try:
        entities = _ner(normalize_for_ner(text))
    except Exception as e:
        logger.warning(f"{_MODEL_ID} error: {e}")
        return []

    tuples = _spans_tuple_for_text(text, entities, config)
    return [Span(start=s, end=e, tag=t) for s, e, t in tuples]
