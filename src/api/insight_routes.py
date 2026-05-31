from importlib import import_module

from flask import Blueprint, Response, jsonify, request

insight_bp = Blueprint("insight", __name__)
generation = import_module("src.pipeline.04_generation.service")
settings = import_module("src.config.settings")
llama_cpp_models = import_module("src.pipeline.04_generation.llama_cpp_models")


@insight_bp.route("/api/theme-summary", methods=["POST"])
def theme_summary():
    try:
        data = request.get_json(silent=True) or {}
        payload = generation.generate_theme_summary(
            theme_name=data.get("theme", ""),
            theme_query=data.get("query", ""),
            llm_model=data.get("llm_model") or settings.DEFAULT_LLM_MODEL,
            allow_model_download=bool(data.get("allow_model_download", False)),
            provider=data.get("provider", settings.DEFAULT_LLM_PROVIDER),
            filters=_filters_from_payload(data),
        )
        return jsonify(payload)
    except ValueError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except generation.LocalModelConnectionError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 503
    except Exception as exc:
        print(f"[LLAMA_CPP ERROR] {str(exc)}")
        return jsonify({"status": "error", "error": str(exc)}), 500


@insight_bp.route("/api/clear-cache", methods=["POST"])
def clear_cache():
    try:
        return jsonify(generation.clear_insight_cache())
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@insight_bp.route("/api/precompute-insights", methods=["POST"])
def precompute_insights():
    data = request.get_json(silent=True) or {}
    themes = data.get("themes", [])
    if not themes:
        return jsonify({"error": "No themes provided"}), 400

    return Response(
        generation.precompute_insights_stream(
            themes=themes,
            llm_model=data.get("llm_model") or settings.DEFAULT_LLM_MODEL,
            custom_prompt=data.get("custom_prompt", ""),
            allow_model_download=bool(data.get("allow_model_download", False)),
            provider=data.get("provider", settings.DEFAULT_LLM_PROVIDER),
            filters=_filters_from_payload(data),
        ),
        mimetype="application/x-ndjson",
    )


@insight_bp.route("/api/llm-models", methods=["GET"])
def llm_models():
    return jsonify(
        {
            "default_provider": settings.DEFAULT_LLM_PROVIDER,
            "default_model": settings.DEFAULT_LLM_MODEL,
            "llama_cpp_base_url": settings.LLAMA_CPP_BASE_URL,
            "models": llama_cpp_models.llama_cpp_model_options(),
        }
    )


@insight_bp.route("/api/themes-overview", methods=["GET"])
def get_themes_overview():
    filters = {}
    for key in [
        "institution",
        "academic_year",
        "location",
        "programme",
        "study_mode",
        "cohort",
    ]:
        value = request.args.get(key)
        if value and value != "All":
            filters[key] = value
    return jsonify(generation.themes_overview_payload(filters))


def _filters_from_payload(data: dict) -> dict:
    raw_filters = data.get("filters") or {}
    if not isinstance(raw_filters, dict):
        raw_filters = {}
    filters = {}
    for key in [
        "institution",
        "academic_year",
        "location",
        "programme",
        "study_mode",
        "cohort",
    ]:
        value = raw_filters.get(key) or data.get(key)
        if value and value not in {"All", "all"}:
            filters[key] = value
    return filters
