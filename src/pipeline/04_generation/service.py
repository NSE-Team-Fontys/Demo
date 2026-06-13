from importlib import import_module
import json

from src.config.settings import (
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
    HIERARCHICAL_RAG_BATCH_DOCUMENTS,
    HIERARCHICAL_RAG_MAX_DOCUMENTS,
    INSIGHT_CACHE_VERSION,
    LLM_CONTEXT_DOCUMENTS,
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

HIERARCHICAL_RAG_STRATEGY = "semantic_theme_map_reduce_v1"


def _model_generation_settings(provider: str, llm_model: str) -> dict | None:
    selected = (provider or DEFAULT_LLM_PROVIDER).strip().lower()
    if selected not in {"llama.cpp", "llamacpp", "llama-cpp"}:
        return None
    return llama_cpp_models.resolve_llama_cpp_model(llm_model).generation.to_dict()


def _normalized_filters(filters: dict | None) -> dict:
    return {
        str(key): str(value)
        for key, value in sorted((filters or {}).items())
        if value is not None and str(value).strip() and str(value).lower() != "all"
    }


def _cache_key(theme_name: str, filters: dict | None = None, theme_query: str | None = None) -> str:
    normalized = _normalized_filters(filters)
    key = theme_name
    if theme_query and theme_query != theme_name:
        key = f"{theme_name}::subquery={theme_query}"
    if not normalized:
        return key
    filters_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return f"{key}::filters={filters_json}"


def _cache_filters_match(cached_data: dict | None, filters: dict | None) -> bool:
    if not isinstance(cached_data, dict):
        return False
    return _normalized_filters(cached_data.get("filters_applied")) == _normalized_filters(
        filters
    )


def _cached_dashboard_response(
    cache: dict,
    theme_name: str,
    *,
    filters: dict | None = None,
    llm_provider: str | None = None,
    llm_model: str | None = None,
    llm_generation_settings: dict | None = None,
    match_llm_identity: bool = False,
) -> dict | None:
    cached_data = cache.get(_cache_key(theme_name, filters))
    if not cache_has_full_dashboard_payload(
        cached_data,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_generation_settings=llm_generation_settings,
        match_llm_identity=match_llm_identity,
    ) or not _cache_filters_match(cached_data, filters):
        return None
    response_data = dict(cached_data)
    response_data["status"] = "success"
    response_data.setdefault("theme", theme_name)
    return response_data


def _select_theme_documents(
    collection,
    theme_name: str,
    *,
    filters: dict | None = None,
    theme_query: str | None = None,
    max_documents: int | None = None,
):
    cap = max_documents if max_documents and max_documents > 0 else HIERARCHICAL_RAG_MAX_DOCUMENTS
    embedding_model = retrieval.collection_embedding_model(collection)
    if theme_query and theme_query != theme_name:
        collected = retrieval.collect_documents_by_query(
            collection,
            theme_query,
            filters=_normalized_filters(filters),
            model_id=embedding_model,
            n_results=cap or 500,
        )
    else:
        collected = retrieval.collect_theme_documents(
            collection,
            theme_name,
            filters=_normalized_filters(filters),
            model_id=embedding_model,
        )
    all_docs = collected["documents"]
    selected_docs = all_docs[:cap] if cap > 0 else all_docs
    return {
        "frequency": collected["frequency"],
        "vector_relevant_count": collected["vector_relevant_count"],
        "total_filtered_documents": collected["total_filtered_documents"],
        "relevant_docs": selected_docs,
        "all_docs": all_docs,
        "source_document_count": len(all_docs),
        "analyzed_document_count": len(selected_docs),
    }


def _document_batches(docs: list[str]) -> list[list[str]]:
    batch_size = max(1, HIERARCHICAL_RAG_BATCH_DOCUMENTS)
    return [docs[i : i + batch_size] for i in range(0, len(docs), batch_size)]


def _generate_hierarchical_json(
    client,
    llm_model: str,
    theme_name: str,
    docs: list[str],
    *,
    custom_prompt: str = "",
) -> dict:
    batches = _document_batches(docs)
    if len(batches) <= 1:
        prompt = prompts.build_prompt(theme_name, docs, custom_prompt=custom_prompt)
        return prompts.parse_llm_json(client.generate_json(llm_model, prompt, timeout=600))

    batch_summaries = []
    for i, batch in enumerate(batches, start=1):
        prompt = prompts.build_batch_summary_prompt(
            theme_name,
            batch,
            batch_number=i,
            total_batches=len(batches),
            custom_prompt=custom_prompt,
        )
        parsed = prompts.parse_llm_json(
            client.generate_json(llm_model, prompt, timeout=600)
        )
        parsed["batch_number"] = i
        parsed["source_document_count"] = len(batch)
        batch_summaries.append(parsed)

    reduce_prompt = prompts.build_reduce_prompt(
        theme_name,
        batch_summaries,
        source_document_count=len(docs),
    )
    return prompts.parse_llm_json(
        client.generate_json(llm_model, reduce_prompt, timeout=600)
    )


def _generate_theme_payload(
    *,
    client,
    collection,
    theme_name: str,
    filters: dict,
    provider: str,
    llm_model: str,
    llm_generation_settings: dict | None,
    custom_prompt: str = "",
    theme_query: str | None = None,
    max_documents: int | None = None,
) -> dict:
    selected = _select_theme_documents(collection, theme_name, filters=filters, theme_query=theme_query, max_documents=max_documents)
    relevant_docs = selected["relevant_docs"]
    if not relevant_docs:
        return _empty_theme_payload(
            theme_name,
            selected,
            filters=filters,
            provider=provider,
            llm_model=llm_model,
            llm_generation_settings=llm_generation_settings,
        )

    parsed = _generate_hierarchical_json(
        client,
        llm_model,
        theme_name,
        relevant_docs,
        custom_prompt=custom_prompt,
    )
    return _theme_payload_from_parsed(
        theme_name,
        selected,
        parsed,
        filters=filters,
        provider=provider,
        llm_model=llm_model,
        llm_generation_settings=llm_generation_settings,
    )


def generate_theme_summary(
    *,
    theme_name: str,
    theme_query: str,
    llm_model: str = DEFAULT_LLM_MODEL,
    allow_model_download: bool = False,
    provider: str = DEFAULT_LLM_PROVIDER,
    filters: dict | None = None,
) -> dict:
    llm_model = str(llm_model or DEFAULT_LLM_MODEL).strip()
    provider = str(provider or DEFAULT_LLM_PROVIDER).strip()
    filters = _normalized_filters(filters)
    llm_generation_settings = _model_generation_settings(provider, llm_model)
    is_subquery = theme_query and theme_query != theme_name
    if not theme_name and not theme_query:
        raise ValueError("No query provided")

    cache = load_cache()
    cache_key = _cache_key(theme_name, filters, theme_query if is_subquery else None)
    if not is_subquery:
        cached_response = _cached_dashboard_response(
            cache,
            theme_name,
            filters=filters,
            llm_provider=provider,
            llm_model=llm_model,
            llm_generation_settings=llm_generation_settings,
            match_llm_identity=True,
        )
        if cached_response is not None:
            print(f"[LLM] Returning cached summary for: {theme_name}")
            return cached_response
    elif cache_key in cache:
        print(f"[LLM] Returning cached subquery summary for: {theme_query}")
        return cache[cache_key]

    if cache_key in cache and not is_subquery:
        print(
            f"[LLM] Cached summary for {theme_name} is missing current "
            "dashboard fields; regenerating."
        )

    client = get_llm_client(provider)
    try:
        label = theme_query if is_subquery else theme_name
        print(f"[LLM] Cache miss - generating summary for: {label}")
        client.ensure_model_available(llm_model, allow_download=allow_model_download)

        collection = retrieval.get_collection()
        response_data = _generate_theme_payload(
            client=client,
            collection=collection,
            theme_name=theme_name,
            filters=filters,
            provider=provider,
            llm_model=llm_model,
            llm_generation_settings=llm_generation_settings,
            theme_query=theme_query if is_subquery else None,
        )
        print(
            f"[LLM] Hierarchical RAG analyzed "
            f"{response_data['hierarchical_document_count']} / "
            f"{response_data['document_count']} semantically assigned docs for "
            f"{theme_name}."
        )

        cache[cache_key] = response_data
        save_cache(cache)
        print(f"[LLM] Saved summary to cache for: {theme_name}")

        return response_data
    finally:
        client.unload(llm_model)


def _empty_theme_payload(
    theme_name: str,
    selected: dict,
    *,
    filters: dict,
    provider: str,
    llm_model: str,
    llm_generation_settings: dict | None,
) -> dict:
    return {
        "status": "success",
        "theme": theme_name,
        "frequency": selected["frequency"],
        "document_count": selected["source_document_count"],
        "vector_relevant_count": selected["vector_relevant_count"],
        "total_filtered_documents": selected["total_filtered_documents"],
        "llm_document_count": 0,
        "hierarchical_document_count": 0,
        "hierarchical_batch_documents": HIERARCHICAL_RAG_BATCH_DOCUMENTS,
        "rag_strategy": HIERARCHICAL_RAG_STRATEGY,
        "filters_applied": filters,
        "cache_version": INSIGHT_CACHE_VERSION,
        "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
        "llm_provider": provider,
        "llm_model": llm_model,
        "llm_generation_settings": llm_generation_settings,
        "reranker": retrieval.current_reranker_id(),
        "summary": "No responses were semantically assigned to this theme.",
        "sentiments": [],
        "positive_comments": [],
        "critical_comments": [],
        "student_suggestions": [],
        "subthemes": [],
        "subtheme_mentions": [],
        "quotes": [],
    }


def _theme_payload_from_parsed(
    theme_name: str,
    selected: dict,
    parsed: dict,
    *,
    filters: dict,
    provider: str,
    llm_model: str,
    llm_generation_settings: dict | None,
) -> dict:
    relevant_docs = selected["relevant_docs"]
    all_docs = selected.get("all_docs", relevant_docs)
    quotes = [doc for doc in all_docs if len(doc.strip()) > 1]
    sentiments = parsed.get("sentiments", [])
    subthemes = parsed.get("subthemes", [])
    return {
        "status": "success",
        "theme": theme_name,
        "frequency": selected["frequency"],
        "document_count": selected["source_document_count"],
        "vector_relevant_count": selected["vector_relevant_count"],
        "total_filtered_documents": selected["total_filtered_documents"],
        "llm_document_count": selected["analyzed_document_count"],
        "hierarchical_document_count": selected["analyzed_document_count"],
        "hierarchical_batch_documents": HIERARCHICAL_RAG_BATCH_DOCUMENTS,
        "rag_strategy": HIERARCHICAL_RAG_STRATEGY,
        "filters_applied": filters,
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
        "subthemes": subthemes,
        "subtheme_mentions": insight_metrics.subtheme_mention_rows(subthemes, all_docs),
        "quotes": quotes,
    }


def precompute_insights_stream(
    *,
    themes: list[dict],
    llm_model: str = DEFAULT_LLM_MODEL,
    custom_prompt: str = "",
    allow_model_download: bool = False,
    provider: str = DEFAULT_LLM_PROVIDER,
    filters: dict | None = None,
    max_documents: int | None = None,
    filter_grid: list[dict] | None = None,
    precache_subthemes: bool = False,
):
    llm_model = str(llm_model or DEFAULT_LLM_MODEL).strip()
    provider = str(provider or DEFAULT_LLM_PROVIDER).strip()
    filters = _normalized_filters(filters)
    normalized_grid = [_normalized_filters(combo) for combo in (filter_grid or [])]
    # Drop combos equal to the baseline so we don't duplicate work
    baseline_key = json.dumps(filters, sort_keys=True)
    normalized_grid = [
        combo for combo in normalized_grid
        if json.dumps(combo, sort_keys=True) != baseline_key
    ]
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
                filters=filters,
                llm_provider=provider,
                llm_model=llm_model,
                llm_generation_settings=llm_generation_settings,
                match_llm_identity=True,
            )
            is not None
        }
        if len(cached_theme_names) == len(themes) and not normalized_grid:
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

        for i, theme in enumerate(themes):
            theme_name = theme.get("name")

            if (
                _cached_dashboard_response(
                    cache,
                    theme_name,
                    filters=filters,
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
                    "message": f"Collecting semantically assigned answers for {theme_name}...",
                }
            ) + "\n"

            yield json.dumps(
                {
                    "status": "progress",
                    "theme": theme_name,
                    "progress": int(((i + 0.5) / len(themes)) * 100),
                    "message": (
                        f"{llm_model} is generating hierarchical summary for "
                        f"{theme_name}..."
                    ),
                }
            ) + "\n"

            try:
                response_data = _generate_theme_payload(
                    client=client,
                    collection=collection,
                    theme_name=theme_name,
                    filters=filters,
                    provider=provider,
                    llm_model=llm_model,
                    llm_generation_settings=llm_generation_settings,
                    custom_prompt=custom_prompt,
                    max_documents=max_documents,
                )
                cache[_cache_key(theme_name, filters)] = response_data
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

        # Optional pre-cache pass: cross-product of filter combinations.
        if normalized_grid:
            total_combos = len(normalized_grid)
            for combo_idx, combo in enumerate(normalized_grid):
                combo_label = ", ".join(f"{k}={v}" for k, v in combo.items()) or "baseline"
                for j, theme in enumerate(themes):
                    theme_name = theme.get("name")
                    overall_step = combo_idx * len(themes) + j
                    overall_total = total_combos * len(themes)
                    base_progress = int((overall_step / max(overall_total, 1)) * 100)

                    if (
                        _cached_dashboard_response(
                            cache,
                            theme_name,
                            filters=combo,
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
                                "progress": base_progress,
                                "message": (
                                    f"[combo {combo_idx + 1}/{total_combos}: {combo_label}] "
                                    f"Cached: {theme_name}"
                                ),
                            }
                        ) + "\n"
                        continue

                    yield json.dumps(
                        {
                            "status": "progress",
                            "theme": theme_name,
                            "progress": base_progress,
                            "message": (
                                f"[combo {combo_idx + 1}/{total_combos}: {combo_label}] "
                                f"Generating {theme_name}..."
                            ),
                        }
                    ) + "\n"

                    try:
                        response_data = _generate_theme_payload(
                            client=client,
                            collection=collection,
                            theme_name=theme_name,
                            filters=combo,
                            provider=provider,
                            llm_model=llm_model,
                            llm_generation_settings=llm_generation_settings,
                            custom_prompt=custom_prompt,
                            max_documents=max_documents,
                        )
                        cache[_cache_key(theme_name, combo)] = response_data
                    except Exception as exc:
                        yield json.dumps(
                            {
                                "status": "progress",
                                "theme": theme_name,
                                "message": (
                                    f"[combo {combo_idx + 1}/{total_combos}: {combo_label}] "
                                    f"Skipped {theme_name}: {str(exc)}"
                                ),
                                "progress": base_progress,
                            }
                        ) + "\n"
                        continue
                    save_cache(cache)

                    if precache_subthemes:
                        subthemes = [
                            str(s).strip()
                            for s in (response_data.get("subthemes") or [])
                            if str(s).strip() and str(s).strip() != theme_name
                        ]
                        for st_idx, subtheme in enumerate(subthemes):
                            sub_key = _cache_key(theme_name, combo, subtheme)
                            if sub_key in cache:
                                continue
                            yield json.dumps(
                                {
                                    "status": "progress",
                                    "theme": theme_name,
                                    "progress": base_progress,
                                    "message": (
                                        f"[combo {combo_idx + 1}/{total_combos}: {combo_label}] "
                                        f"Sub-theme {st_idx + 1}/{len(subthemes)}: {subtheme}"
                                    ),
                                }
                            ) + "\n"
                            try:
                                sub_data = _generate_theme_payload(
                                    client=client,
                                    collection=collection,
                                    theme_name=theme_name,
                                    filters=combo,
                                    provider=provider,
                                    llm_model=llm_model,
                                    llm_generation_settings=llm_generation_settings,
                                    custom_prompt=custom_prompt,
                                    max_documents=max_documents,
                                    theme_query=subtheme,
                                )
                                cache[sub_key] = sub_data
                                save_cache(cache)
                            except Exception as exc:
                                yield json.dumps(
                                    {
                                        "status": "progress",
                                        "theme": theme_name,
                                        "message": (
                                            f"[combo {combo_idx + 1}/{total_combos}: {combo_label}] "
                                            f"Sub-theme skipped {subtheme}: {str(exc)}"
                                        ),
                                        "progress": base_progress,
                                    }
                                ) + "\n"
                                continue

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
    normalized_filters = _normalized_filters(filters)
    cached_values = [
        data
        for data in load_cache().values()
        if cache_has_full_dashboard_payload(data)
    ]
    cache = {
        data.get("theme"): data
        for data in cached_values
        if _cache_filters_match(data, {})
    }
    if not normalized_filters:
        return cache

    exact_filter_cache = {
        data.get("theme"): data
        for data in cached_values
        if _cache_filters_match(data, normalized_filters)
    }
    try:
        filtered_cache = retrieval.filtered_themes_overview(cache, normalized_filters)
        return {**filtered_cache, **exact_filter_cache}
    except Exception as exc:
        print(f"[DYNAMIC FILTER ERROR] {str(exc)}")
        return {**cache, **exact_filter_cache}
