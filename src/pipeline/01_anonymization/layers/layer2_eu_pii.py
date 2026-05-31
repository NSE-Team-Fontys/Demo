from __future__ import annotations

import logging
import os
import re
from typing import Optional

import torch
from transformers import pipeline as hf_pipeline

from src.utils.model_device import describe_model_device, get_model_device, get_pipeline_device

from .layer2_text_norm import normalize_for_ner

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_torch_device = get_model_device()
_device = get_pipeline_device(_torch_device)
_use_fp16 = os.environ.get("LAYER2_FP16", "").lower() in {"1", "true", "yes"}

logger.info(
    "Loading tabularisai/eu-pii-safeguard model on %s (downloads on first run)...",
    describe_model_device(_torch_device),
)
try:
    pipeline_kwargs = {
        "task": "token-classification",
        "model": "tabularisai/eu-pii-safeguard",
        "aggregation_strategy": "simple",
        "device": _device,
    }
    if _torch_device != "cpu" and _use_fp16:
        pipeline_kwargs["model_kwargs"] = {"torch_dtype": torch.float16}
        logger.info("LAYER2_FP16 enabled for eu-pii-safeguard.")
    _ner = hf_pipeline(**pipeline_kwargs)
    logger.info("eu-pii-safeguard loaded successfully.")
    _load_error = None
except Exception as e:
    _ner = None
    _load_error = e
    logger.warning(f"eu-pii-safeguard failed to load: {e}. Layer will be skipped.")


def unload_models() -> None:
    global _ner
    _ner = None
    import gc
    gc.collect()
    if torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()


def ensure_eu_pii_available() -> None:
    """Raise a clear error if the selected EU-PII layer is unavailable."""
    if _ner is None:
        detail = f" ({_load_error})" if _load_error else ""
        raise RuntimeError(
            "EU-PII-Safeguard is selected but the model could not be loaded. "
            "Check your internet/HF_TOKEN for first download, or remove this layer."
            + detail
        )


def _eu_pii_tag(entity_group: str) -> str:
    label = (entity_group or "").upper()
    if any(k in label for k in ("NAME", "PERSON", "FIRSTNAME", "LASTNAME", "SURNAME", "GIVENNAME")):
        return "[NAME]"
    if any(k in label for k in ("CITY", "ADDRESS", "STREET", "LOCATION", "ZIPCODE", "POSTAL", "STATE", "COUNTRY", "REGION")):
        return "[LOCATION]"
    if any(k in label for k in ("HEALTH", "MEDICAL", "CONDITION", "DIAGNOSIS", "ILLNESS", "DISEASE", "DISABILITY", "MEDICATION")):
        return "[HEALTH]"
    return "[PII]"


def _config_allows_tag(config: Optional[dict], tag: str) -> bool:
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


def _apply_entities(text: str, entities: list, config: Optional[dict]) -> str:
    if not entities:
        return text

    entities_sorted = sorted(entities, key=lambda e: e["end"] - e["start"], reverse=True)
    result = text
    replaced = []
    for ent in entities_sorted:
        span = text[ent["start"] : ent["end"]]
        if not span.strip() or len(span) < 2:
            continue
        label = ent.get("entity_group", "")
        tag = _eu_pii_tag(label)
        if not _config_allows_tag(config, tag):
            continue

        # Same idea as privacy_officer: robust replacement regardless of offsets
        pattern = re.compile(re.escape(span), re.IGNORECASE)
        new_result = pattern.sub(tag, result)
        if new_result != result:
            replaced.append(f"'{span}' ({label} -> {tag})")
            result = new_result
    if replaced:
        logger.info("eu-pii-safeguard caught %s additional entities: %s", len(replaced), ", ".join(replaced))
    return result


def eu_pii_collect_batch(texts: list, config: Optional[dict] = None) -> list:
    """
    Run eu-pii-safeguard on normalized texts; return [(start,end,tag), …] per text.
    Same contract as privacy_officer (late masking).
    """
    ensure_eu_pii_available()
    if not texts:
        return [[] for _ in texts]
    try:
        texts_for_ner = [normalize_for_ner(t) if isinstance(t, str) else "" for t in texts]
        batch_entities = _ner(texts_for_ner, batch_size=len(texts_for_ner))
    except Exception as e:
        logger.warning("eu-pii-safeguard collect batch error: %s", e)
        return [[] for _ in texts]

    all_spans = []
    for text, entities in zip(texts, batch_entities):
        if not isinstance(text, str):
            all_spans.append([])
            continue
        spans = []
        for ent in sorted(entities, key=lambda e: e["end"] - e["start"], reverse=True):
            span_text = text[ent["start"] : ent["end"]]
            if not span_text.strip() or len(span_text) < 2:
                continue
            tag = _eu_pii_tag(ent.get("entity_group", ""))
            if not _config_allows_tag(config, tag):
                continue
            spans.append((ent["start"], ent["end"], tag))
        all_spans.append(spans)
    return all_spans


def eu_pii_safeguard_anonymize(text: str, config: Optional[dict] = None) -> str:
    """Layer 2 masking (no span plumbing): returns text with tags."""
    ensure_eu_pii_available()
    if not isinstance(text, str) or not text.strip():
        return text
    try:
        entities = _ner(normalize_for_ner(text))
    except Exception as e:
        logger.warning(f"eu-pii-safeguard error: {e}")
        return text
    return _apply_entities(text, entities, config)


def eu_pii_safeguard_anonymize_batch(texts: list, config: Optional[dict] = None) -> list:
    """
    Run eu-pii-safeguard on a list of texts in one pipeline call.
    Kept aligned with privacy_officer for callers that want direct batch masking.
    """
    ensure_eu_pii_available()
    if not texts:
        return texts
    try:
        batch_entities = _ner(texts, batch_size=len(texts))
    except Exception as e:
        logger.warning("eu-pii-safeguard batch error: %s", e)
        return texts
    return [_apply_entities(text, entities, config) for text, entities in zip(texts, batch_entities)]


def eu_pii_masking_spec() -> dict:
    return {
        "[NAME]": ["*NAME*", "*PERSON*"],
        "[LOCATION]": ["*ADDRESS*", "*CITY*", "*ZIPCODE*", "*LOCATION*"],
        "[HEALTH]": ["*HEALTH*", "*MEDICAL*", "*CONDITION*", "*DIAGNOSIS*", "*ILLNESS*", "*DISEASE*", "*DISABILITY*", "*MEDICATION*"],
        "[PII]": ["(everything else: email/phone/iban/ids/etc.)"],
    }
