from importlib import import_module
import json

from src.config.paths import CACHE_FILE, SUBTHEME_CACHE_FILE
from src.config.settings import (
    HIERARCHICAL_RAG_BATCH_DOCUMENTS,
    INSIGHT_CACHE_VERSION,
    LLM_CONTEXT_DOCUMENTS,
)

retrieval = import_module("src.pipeline.03_retrieval.service")

_cache_data: dict | None = None
_subtheme_cache_data: dict | None = None
_overview_response_cache: dict[str, bytes] = {}


def load_cache() -> dict:
    global _cache_data
    if _cache_data is not None:
        return _cache_data
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                _cache_data = json.load(f)
                return _cache_data
        except Exception:
            pass
    _cache_data = {}
    return _cache_data


def save_cache(cache_data):
    global _cache_data, _overview_response_cache
    tmp_file = CACHE_FILE.with_suffix(f"{CACHE_FILE.suffix}.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, separators=(",", ":"))
    tmp_file.replace(CACHE_FILE)
    _cache_data = cache_data
    _overview_response_cache = {}


def clear_insight_cache() -> dict:
    global _cache_data, _overview_response_cache
    retrieval.clear_runtime_caches()
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    _cache_data = {}
    _overview_response_cache = {}
    return {"status": "success", "message": "Cache cleared"}


def get_overview_response(filter_key: str) -> bytes | None:
    return _overview_response_cache.get(filter_key)


def set_overview_response(filter_key: str, data: bytes) -> None:
    _overview_response_cache[filter_key] = data


def cache_matches_generation_settings(
    cached_theme: dict,
    *,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_generation_settings: dict | None = None,
    match_llm_identity: bool = False,
) -> bool:
    if not isinstance(cached_theme, dict):
        return False
    try:
        classification_metadata = retrieval.classification_cache_metadata()
    except Exception:
        return False
    matches = (
        cached_theme.get("cache_version") == INSIGHT_CACHE_VERSION
        and cached_theme.get("llm_context_documents") == LLM_CONTEXT_DOCUMENTS
        and cached_theme.get("hierarchical_batch_documents")
        == HIERARCHICAL_RAG_BATCH_DOCUMENTS
        and all(
            cached_theme.get(key) == value
            for key, value in classification_metadata.items()
        )
    )
    if match_llm_identity and llm_provider is not None:
        matches = matches and cached_theme.get("llm_provider") == llm_provider
    if match_llm_identity and llm_model is not None:
        matches = matches and cached_theme.get("llm_model") == llm_model
    if llm_generation_settings is not None:
        matches = (
            matches
            and cached_theme.get("llm_generation_settings") == llm_generation_settings
        )
    return matches


def cache_has_full_dashboard_payload(
    cached_theme: dict,
    *,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_generation_settings: dict | None = None,
    match_llm_identity: bool = False,
) -> bool:
    if not cache_matches_generation_settings(
        cached_theme,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_generation_settings=llm_generation_settings,
        match_llm_identity=match_llm_identity,
    ):
        return False

    required_fields = [
        "frequency",
        "vector_relevant_count",
        "llm_document_count",
        "summary",
        "positive_comments",
        "critical_comments",
        "student_suggestions",
        "subthemes",
        "subtheme_manifest",
        "subtheme_mentions",
        "quotes",
    ]
    return all(field in cached_theme for field in required_fields)


def load_subtheme_cache() -> dict:
    global _subtheme_cache_data
    if _subtheme_cache_data is not None:
        return _subtheme_cache_data
    if SUBTHEME_CACHE_FILE.exists():
        try:
            with open(SUBTHEME_CACHE_FILE, "r", encoding="utf-8") as f:
                _subtheme_cache_data = json.load(f)
                return _subtheme_cache_data
        except Exception:
            pass
    _subtheme_cache_data = {}
    return _subtheme_cache_data


def save_subtheme_cache(cache_data):
    global _subtheme_cache_data
    tmp_file = SUBTHEME_CACHE_FILE.with_suffix(f"{SUBTHEME_CACHE_FILE.suffix}.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, separators=(",", ":"))
    tmp_file.replace(SUBTHEME_CACHE_FILE)
    _subtheme_cache_data = cache_data


def clear_subtheme_cache() -> dict:
    global _subtheme_cache_data
    if SUBTHEME_CACHE_FILE.exists():
        SUBTHEME_CACHE_FILE.unlink()
    _subtheme_cache_data = {}
    return {"status": "success", "message": "Subtheme cache cleared"}
