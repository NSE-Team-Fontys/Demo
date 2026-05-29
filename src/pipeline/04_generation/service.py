from importlib import import_module
import json

from src.config.settings import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    INSIGHT_CACHE_VERSION,
    LLM_CONTEXT_DOCUMENTS,
    RERANKER_CANDIDATE_MULTIPLIER,
    RERANKER_MAX_CANDIDATES,
)

cache_store = import_module("src.pipeline.04_generation.cache")
insight_metrics = import_module("src.pipeline.04_generation.insight_metrics")
llm_clients = import_module("src.pipeline.04_generation.llm_clients")
llama_cpp_models = import_module("src.pipeline.04_generation.llama_cpp_models")
prompts = import_module("src.pipeline.04_generation.prompts")
retrieval = import_module("src.pipeline.03_retrieval.service")
LocalModelConnectionError = llm_clients.LocalModelConnectionError
get_llm_client = llm_clients.get_llm_client

load_cache = cache_store.load_cache
save_cache = cache_store.save_cache
clear_insight_cache = cache_store.clear_insight_cache
cache_matches_generation_settings = cache_store.cache_matches_generation_settings
cache_has_full_dashboard_payload = cache_store.cache_has_full_dashboard_payload


def _model_generation_settings(provider: str, llm_model: str) -> dict | None:
    selected = (provider or DEFAULT_LLM_PROVIDER).strip().lower()
    if selected not in {"llama.cpp", "llamacpp", "llama-cpp"}:
        return None
    return llama_cpp_models.resolve_llama_cpp_model(llm_model).generation.to_dict()


def _cached_dashboard_response(
    cache: dict,
    theme_name: str,
    *,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_generation_settings: dict | None = None,
    match_llm_identity: bool = False,
) -> dict | None:
    cached_data = cache.get(theme_name)
    if not cache_has_full_dashboard_payload(
        cached_data,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_generation_settings=llm_generation_settings,
        match_llm_identity=match_llm_identity,
    ):
        return None
    response_data = dict(cached_data)
    response_data["status"] = "success"
    response_data.setdefault("theme", theme_name)
    return response_data


def _select_theme_documents(
    collection,
    theme_name: str,
    query: str,
    *,
    allow_model_download: bool,
):
    embedding_model = retrieval.collection_embedding_model(collection)
    model = retrieval.get_theme_embedding_model(embedding_model)
    query_embedding = model.encode(query, normalize_embeddings=True)
    total_docs = collection.count()
    distribution = retrieval.theme_distribution(collection, embedding_model)
    retrieval_k = min(
        max(20 * RERANKER_CANDIDATE_MULTIPLIER, 20),
        max(total_docs, 1),
        RERANKER_MAX_CANDIDATES,
    )

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=retrieval_k,
        include=["documents", "distances"],
    )

    relevant_docs = []
    relevant_distances = []
    if results["documents"] and len(results["documents"]) > 0:
        for i, doc in enumerate(results["documents"][0]):
            relevant_docs.append(doc)
            relevant_distances.append(results["distances"][0][i])

    ranked_docs = retrieval.rerank_documents(
        query,
        relevant_docs[:RERANKER_MAX_CANDIDATES],
        distances=relevant_distances[:RERANKER_MAX_CANDIDATES],
        top_n=RERANKER_MAX_CANDIDATES,
        allow_model_download=allow_model_download,
    )
    selected_docs = [item["document"] for item in ranked_docs]
    return {
        "frequency": distribution["percentages"].get(theme_name, 0),
        "vector_relevant_count": distribution["counts"].get(theme_name, len(relevant_docs)),
        "relevant_docs": selected_docs,
        "llm_docs": selected_docs[:LLM_CONTEXT_DOCUMENTS],
    }


def generate_theme_summary(
    *,
    theme_name: str,
    theme_query: str,
    llm_model: str = DEFAULT_LLM_MODEL,
    allow_model_download: bool = False,
    provider: str = DEFAULT_LLM_PROVIDER,
) -> dict:
    llm_model = str(llm_model or DEFAULT_LLM_MODEL).strip()
    provider = str(provider or DEFAULT_LLM_PROVIDER).strip()
    llm_generation_settings = _model_generation_settings(provider, llm_model)
    theme_search_query = retrieval.theme_query_text(theme_name) if theme_name else theme_query
    if not theme_search_query:
        raise ValueError("No query provided")

    cache = load_cache()
    cached_response = _cached_dashboard_response(
        cache,
        theme_name,
        llm_provider=provider,
        llm_model=llm_model,
        llm_generation_settings=llm_generation_settings,
        match_llm_identity=True,
    )
    if cached_response is not None:
        print(f"[LLM] Returning cached summary for: {theme_name}")
        return cached_response
    if theme_name in cache:
        print(
            f"[LLM] Cached summary for {theme_name} is missing current "
            "dashboard fields; regenerating."
        )

    client = get_llm_client(provider)
    try:
        print(f"[LLM] Cache miss - generating summary for: {theme_name}")
        client.ensure_model_available(llm_model, allow_download=allow_model_download)

        collection = retrieval.get_collection()
        selected = _select_theme_documents(
            collection,
            theme_name,
            theme_search_query,
            allow_model_download=allow_model_download,
        )
        relevant_docs = selected["relevant_docs"]
        llm_docs = selected["llm_docs"]
        prompt = prompts.build_prompt(theme_name, llm_docs)
        real_quotes = relevant_docs[:3] if len(relevant_docs) >= 3 else relevant_docs

        print(
            f"[LLM] Reranked {selected['vector_relevant_count']} relevant docs; "
            f"sending {len(llm_docs)} docs to local {provider}..."
        )
        result_text = client.generate_json(llm_model, prompt, timeout=600)
        print(f"[LLM] Raw response received: {result_text}")
        parsed = prompts.parse_llm_json(result_text)

        sentiments = parsed.get("sentiments", [])
        response_data = {
            "status": "success",
            "theme": theme_name,
            "frequency": selected["frequency"],
            "document_count": len(relevant_docs),
            "vector_relevant_count": selected["vector_relevant_count"],
            "llm_document_count": len(llm_docs),
            "cache_version": INSIGHT_CACHE_VERSION,
            "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
            "llm_provider": provider,
            "llm_model": llm_model,
            "llm_generation_settings": llm_generation_settings,
            "reranker": retrieval.current_reranker_id(),
            "summary": parsed.get("summary", "Summary could not be parsed."),
            "sentiments": sentiments,
            "positive_comments": parsed.get("positive_comments", [])[:3],
            "critical_comments": parsed.get("critical_comments", [])[:3],
            "student_suggestions": parsed.get("student_suggestions", [])[:3],
            "subthemes": parsed.get("subthemes", []),
            "subtheme_mentions": insight_metrics.subtheme_mention_rows(
                parsed.get("subthemes", []), relevant_docs
            ),
            "quotes": real_quotes,
        }

        if sentiments:
            cache[theme_name] = response_data
            save_cache(cache)
            print(f"[LLM] Saved summary to cache for: {theme_name}")

        return response_data
    finally:
        client.unload(llm_model)


def precompute_insights_stream(
    *,
    themes: list[dict],
    llm_model: str = DEFAULT_LLM_MODEL,
    custom_prompt: str = "",
    allow_model_download: bool = False,
    provider: str = DEFAULT_LLM_PROVIDER,
):
    llm_model = str(llm_model or DEFAULT_LLM_MODEL).strip()
    provider = str(provider or DEFAULT_LLM_PROVIDER).strip()
    client = None
    try:
        llm_generation_settings = _model_generation_settings(provider, llm_model)
        cache = load_cache()
        cached_theme_names = {
            theme.get("name")
            for theme in themes
            if _cached_dashboard_response(
                cache,
                theme.get("name"),
                llm_provider=provider,
                llm_model=llm_model,
                llm_generation_settings=llm_generation_settings,
                match_llm_identity=True,
            )
            is not None
        }
        if len(cached_theme_names) == len(themes):
            for i, theme in enumerate(themes):
                theme_name = theme.get("name")
                yield json.dumps(
                    {
                        "status": "progress",
                        "theme": theme_name,
                        "progress": int(((i + 1) / len(themes)) * 100),
                        "message": f"Loaded cached insights for {theme_name}",
                    }
                ) + "\n"
            yield json.dumps(
                {
                    "status": "success",
                    "message": "All insights already cached!",
                    "progress": 100,
                }
            ) + "\n"
            return

        yield json.dumps(
            {
                "status": "progress",
                "progress": 1,
                "message": f"Checking {provider} model '{llm_model}'...",
            }
        ) + "\n"

        client = get_llm_client(provider)
        client.ensure_model_available(llm_model, allow_download=allow_model_download)

        collection = retrieval.get_collection()
        embedding_model = retrieval.collection_embedding_model(collection)
        distribution = retrieval.theme_distribution(collection, embedding_model)
        model = retrieval.get_theme_embedding_model(embedding_model)

        for i, theme in enumerate(themes):
            theme_name = theme.get("name")
            query = retrieval.theme_query_text(theme_name)

            if (
                _cached_dashboard_response(
                    cache,
                    theme_name,
                    llm_provider=provider,
                    llm_model=llm_model,
                    llm_generation_settings=llm_generation_settings,
                    match_llm_identity=True,
                )
                is not None
            ):
                yield json.dumps(
                    {
                        "status": "progress",
                        "theme": theme_name,
                        "progress": int(((i + 1) / len(themes)) * 100),
                        "message": f"Loaded cached insights for {theme_name}",
                    }
                ) + "\n"
                continue

            yield json.dumps(
                {
                    "status": "progress",
                    "theme": theme_name,
                    "progress": int((i / len(themes)) * 100),
                    "message": f"Querying VectorDB for {theme_name}...",
                }
            ) + "\n"

            query_embedding = model.encode(query, normalize_embeddings=True)
            retrieval_k = min(RERANKER_MAX_CANDIDATES, max(collection.count(), 1))
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=retrieval_k,
                include=["documents", "distances"],
            )

            relevant_docs = []
            relevant_distances = []
            if results["documents"] and len(results["documents"]) > 0:
                for j, doc in enumerate(results["documents"][0]):
                    relevant_docs.append(doc)
                    relevant_distances.append(results["distances"][0][j])

            vector_relevant_count = distribution["counts"].get(theme_name, len(relevant_docs))
            ranked_docs = retrieval.rerank_documents(
                query,
                relevant_docs[:RERANKER_MAX_CANDIDATES],
                distances=relevant_distances[:RERANKER_MAX_CANDIDATES],
                top_n=RERANKER_MAX_CANDIDATES,
                allow_model_download=allow_model_download,
            )
            relevant_docs = [item["document"] for item in ranked_docs]
            llm_docs = relevant_docs[:LLM_CONTEXT_DOCUMENTS]
            frequency = distribution["percentages"].get(theme_name, 0)

            yield json.dumps(
                {
                    "status": "progress",
                    "theme": theme_name,
                    "progress": int(((i + 0.5) / len(themes)) * 100),
                    "message": (
                        f"{llm_model} is generating summary for "
                        f"{theme_name} with {len(llm_docs)} answers..."
                    ),
                }
            ) + "\n"

            if not relevant_docs:
                cache[theme_name] = {
                    "theme": theme_name,
                    "frequency": frequency,
                    "vector_relevant_count": vector_relevant_count,
                    "llm_document_count": 0,
                    "cache_version": INSIGHT_CACHE_VERSION,
                    "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
                    "llm_provider": provider,
                    "llm_model": llm_model,
                    "llm_generation_settings": llm_generation_settings,
                    "reranker": retrieval.current_reranker_id(),
                    "summary": "Not enough highly relevant responses found.",
                    "sentiments": [],
                    "positive_comments": [],
                    "critical_comments": [],
                    "student_suggestions": [],
                    "subthemes": [],
                    "subtheme_mentions": [],
                    "quotes": [],
                }
                save_cache(cache)
                continue

            prompt = prompts.build_prompt(theme_name, llm_docs, custom_prompt=custom_prompt)
            real_quotes = relevant_docs[:3] if len(relevant_docs) >= 3 else relevant_docs

            try:
                parsed = prompts.parse_llm_json(
                    client.generate_json(llm_model, prompt, timeout=600)
                )
                cache[theme_name] = {
                    "theme": theme_name,
                    "frequency": frequency,
                    "vector_relevant_count": vector_relevant_count,
                    "llm_document_count": len(llm_docs),
                    "cache_version": INSIGHT_CACHE_VERSION,
                    "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
                    "llm_provider": provider,
                    "llm_model": llm_model,
                    "llm_generation_settings": llm_generation_settings,
                    "reranker": retrieval.current_reranker_id(),
                    "summary": parsed.get("summary", "Summary could not be parsed."),
                    "sentiments": parsed.get("sentiments", []),
                    "positive_comments": parsed.get("positive_comments", [])[:3],
                    "critical_comments": parsed.get("critical_comments", [])[:3],
                    "student_suggestions": parsed.get("student_suggestions", [])[:3],
                    "subthemes": parsed.get("subthemes", []),
                    "subtheme_mentions": insight_metrics.subtheme_mention_rows(
                        parsed.get("subthemes", []), relevant_docs
                    ),
                    "quotes": real_quotes,
                }
            except Exception as exc:
                yield json.dumps(
                    {
                        "status": "error",
                        "theme": theme_name,
                        "message": f"Failed to generate summary: {str(exc)}",
                    }
                ) + "\n"
                return
            save_cache(cache)

        yield json.dumps(
            {
                "status": "success",
                "message": "All insights generated!",
                "progress": 100,
            }
        ) + "\n"

    except Exception as exc:
        yield json.dumps({"status": "error", "message": str(exc)}) + "\n"
    finally:
        if client is not None:
            client.unload(llm_model)


def themes_overview_payload(filters: dict) -> dict:
    cache = {
        theme: data
        for theme, data in load_cache().items()
        if cache_has_full_dashboard_payload(data)
    }
    if not filters:
        return cache
    try:
        return retrieval.filtered_themes_overview(cache, filters)
    except Exception as exc:
        print(f"[DYNAMIC FILTER ERROR] {str(exc)}")
        return cache
