from importlib import import_module
import json

from src.config.paths import CACHE_FILE
from src.config.settings import INSIGHT_CACHE_VERSION, LLM_CONTEXT_DOCUMENTS

retrieval = import_module("src.pipeline.03_retrieval.service")


def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache_data):
    tmp_file = CACHE_FILE.with_suffix(f"{CACHE_FILE.suffix}.tmp")
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)
    tmp_file.replace(CACHE_FILE)


def clear_insight_cache() -> dict:
    retrieval.clear_runtime_caches()
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    return {"status": "success", "message": "Cache cleared"}


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
    matches = (
        cached_theme.get("cache_version") == INSIGHT_CACHE_VERSION
        and cached_theme.get("llm_context_documents") == LLM_CONTEXT_DOCUMENTS
        and cached_theme.get("reranker") == retrieval.current_reranker_id()
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
        "sentiments",
        "positive_comments",
        "critical_comments",
        "student_suggestions",
        "subthemes",
        "subtheme_mentions",
        "quotes",
    ]
    return all(field in cached_theme for field in required_fields)
