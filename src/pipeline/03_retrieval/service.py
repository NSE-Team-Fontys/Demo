import chromadb
from importlib import import_module

from src.config.paths import VECTOR_DB_PATH
from src.config.settings import RERANKER_CANDIDATE_MULTIPLIER, RERANKER_MAX_CANDIDATES
from src.config.themes import METADATA_ALIASES, THEME_EMBEDDING_DEFINITIONS, THEMES_LIST

embedding_models = import_module("src.pipeline.02_embedding.embedding_models")
reranker_models = import_module("src.pipeline.03_retrieval.reranker_models")

DEFAULT_EMBEDDING_MODEL = embedding_models.DEFAULT_EMBEDDING_MODEL
describe_embedding_runtime = embedding_models.describe_embedding_runtime
load_embedding_model = embedding_models.load_embedding_model
describe_reranker_runtime = reranker_models.describe_reranker_runtime
load_reranker_model = reranker_models.load_reranker_model
reranker_enabled = reranker_models.reranker_enabled
selected_reranker_model = reranker_models.selected_reranker_model

COLLECTION_NAME = "survey_responses"
THEME_EMBEDDING_MODEL = DEFAULT_EMBEDDING_MODEL

_theme_overview_cache = {}
_theme_embedding_models = {}
_theme_query_embeddings = {}


def metadata_value(meta: dict, canonical_key: str):
    for key in METADATA_ALIASES.get(canonical_key, [canonical_key]):
        value = meta.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def filter_condition(canonical_key: str, value: str):
    aliases = METADATA_ALIASES.get(canonical_key, [canonical_key])
    conditions = [{key: value} for key in aliases]
    if len(conditions) == 1:
        return conditions[0]
    return {"$or": conditions}


def build_where_filter(filters: dict):
    if not filters:
        return None
    conditions = [filter_condition(key, value) for key, value in filters.items()]
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def clear_runtime_caches():
    _theme_overview_cache.clear()


def theme_overview_cache_key(filters: dict) -> tuple:
    return tuple(sorted(filters.items()))


def collection_embedding_model(collection) -> str:
    metadata = getattr(collection, "metadata", None) or {}
    return metadata.get("embedding_model") or THEME_EMBEDDING_MODEL


def get_theme_embedding_model(model_id: str | None = None):
    selected_model = model_id or THEME_EMBEDDING_MODEL
    if selected_model not in _theme_embedding_models:
        print(
            f"[EMBEDDINGS] Loading {selected_model} via "
            f"{describe_embedding_runtime(selected_model)}"
        )
        _theme_embedding_models[selected_model] = load_embedding_model(selected_model)
    return _theme_embedding_models[selected_model]


def theme_query_text(theme_name: str) -> str:
    definition = THEME_EMBEDDING_DEFINITIONS.get(theme_name)
    return f"{theme_name}. {definition}" if definition else theme_name


def get_theme_query_embeddings(model_id: str | None = None):
    selected_model = model_id or THEME_EMBEDDING_MODEL
    if selected_model not in _theme_query_embeddings:
        model = get_theme_embedding_model(selected_model)
        _theme_query_embeddings[selected_model] = {
            theme: model.encode(theme_query_text(theme), normalize_embeddings=True).tolist()
            for theme in THEMES_LIST
        }
    return _theme_query_embeddings[selected_model]


def current_reranker_id():
    return selected_reranker_model() if reranker_enabled() else None


def rerank_documents(
    query: str,
    documents: list[str],
    *,
    metadatas: list[dict] | None = None,
    distances: list[float] | None = None,
    top_n: int | None = None,
    allow_model_download: bool = True,
) -> list[dict]:
    if not documents:
        return []

    if not reranker_enabled():
        ranked = []
        for i, doc in enumerate(documents):
            distance = distances[i] if distances and i < len(distances) else None
            similarity = max(0, 1 - distance) if distance is not None else None
            ranked.append(
                {
                    "document": doc,
                    "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                    "distance": distance,
                    "similarity": similarity,
                    "reranker_score": None,
                }
            )
        return ranked[:top_n] if top_n else ranked

    model_id = selected_reranker_model()
    print(f"[RERANKER] Loading {model_id} via {describe_reranker_runtime(model_id)}")
    model = load_reranker_model(model_id, allow_download=allow_model_download)
    scores = model.predict([(query, doc) for doc in documents])

    ranked = []
    for i, (doc, score) in enumerate(zip(documents, scores)):
        distance = distances[i] if distances and i < len(distances) else None
        similarity = max(0, 1 - distance) if distance is not None else None
        ranked.append(
            {
                "document": doc,
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "distance": distance,
                "similarity": similarity,
                "reranker_score": float(score),
            }
        )

    ranked.sort(key=lambda item: item["reranker_score"], reverse=True)
    return ranked[:top_n] if top_n else ranked


def get_collection():
    return chromadb.PersistentClient(path=str(VECTOR_DB_PATH)).get_collection(
        COLLECTION_NAME
    )


def filter_options_payload() -> dict:
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return {"status": "empty", "options": {}}

    all_docs = collection.get(limit=collection.count())
    buckets = {
        "institutions": set(),
        "academic_years": set(),
        "locations": set(),
        "programmes": set(),
        "study_modes": set(),
        "cohorts": set(),
    }
    bucket_keys = {
        "institutions": "institution",
        "academic_years": "academic_year",
        "locations": "location",
        "programmes": "programme",
        "study_modes": "study_mode",
        "cohorts": "cohort",
    }

    for meta in all_docs.get("metadatas") or []:
        for bucket, canonical_key in bucket_keys.items():
            value = metadata_value(meta, canonical_key)
            if value:
                buckets[bucket].add(str(value))

    return {
        "status": "success",
        "options": {key: sorted(values) for key, values in buckets.items()},
    }


def query_vectors_payload(query_text: str, top_k: int, filters: dict) -> dict:
    if not query_text:
        raise ValueError("Empty query")

    print(f"[QUERY] Searching: '{query_text}' | Filters: {filters}")
    collection = get_collection()
    embedding_model = collection_embedding_model(collection)
    model = get_theme_embedding_model(embedding_model)
    query_embedding = model.encode(query_text, normalize_embeddings=True)
    where_filter = build_where_filter(filters)

    retrieval_k = min(
        max(top_k * RERANKER_CANDIDATE_MULTIPLIER, top_k),
        max(collection.count(), 1),
        RERANKER_MAX_CANDIDATES,
    )
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=retrieval_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    formatted = []
    if results["documents"] and len(results["documents"]) > 0:
        ranked_results = rerank_documents(
            query_text,
            results["documents"][0],
            metadatas=results["metadatas"][0] if results["metadatas"] else None,
            distances=results["distances"][0] if results["distances"] else None,
            top_n=top_k,
        )
        for i, ranked in enumerate(ranked_results):
            doc = ranked["document"]
            similarity = ranked["similarity"] if ranked["similarity"] is not None else 0
            result_item = {
                "id": i + 1,
                "document": doc,
                "preview": doc[:300] + "..." if len(doc) > 300 else doc,
                "similarity": round(similarity, 3),
                "percentage": round(similarity * 100, 1),
                "reranker_score": ranked["reranker_score"],
            }
            if ranked["metadata"]:
                result_item["metadata"] = ranked["metadata"]
            formatted.append(result_item)

    return {
        "status": "success",
        "results": formatted,
        "count": len(formatted),
        "candidate_count": len(results["documents"][0]) if results["documents"] else 0,
        "reranker": current_reranker_id(),
        "query": query_text,
        "filters_applied": filters,
    }


def vector_stats_payload() -> dict:
    client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
    try:
        collection = client.get_collection(COLLECTION_NAME)
    except Exception:
        return {
            "status": "empty",
            "data": [],
            "total_documents": 0,
            "message": "Vector DB not initialized",
        }

    count = collection.count()
    if count == 0:
        return {"status": "empty", "data": [], "total_documents": 0}

    all_docs = collection.get(limit=min(count, 50))
    documents = []
    for i, doc in enumerate((all_docs.get("documents") or [])[:50]):
        documents.append(
            {
                "id": i + 1,
                "text": doc[:200] + "..." if len(doc) > 200 else doc,
                "full_text": doc,
                "metadata": all_docs["metadatas"][i] if all_docs.get("metadatas") else {},
            }
        )

    return {
        "status": "success",
        "data": documents,
        "total_documents": count,
        "samples": len(documents),
    }


def percentages_from_counts(counts: dict[str, int]) -> dict[str, int]:
    total = sum(max(0, int(counts.get(theme, 0))) for theme in THEMES_LIST)
    if total <= 0:
        return {theme: 0 for theme in THEMES_LIST}

    raw = {
        theme: (max(0, int(counts.get(theme, 0))) * 100) / total
        for theme in THEMES_LIST
    }
    percentages = {theme: int(raw[theme]) for theme in THEMES_LIST}
    remainder = 100 - sum(percentages.values())
    by_fraction = sorted(
        THEMES_LIST,
        key=lambda theme: (raw[theme] - percentages[theme], counts.get(theme, 0)),
        reverse=True,
    )
    for theme in by_fraction[:remainder]:
        percentages[theme] += 1
    return percentages


def theme_distribution(collection, model_id: str | None = None, where_filter=None) -> dict:
    if where_filter:
        matching_docs = collection.get(where=where_filter)
        total_docs = (
            len(matching_docs["ids"])
            if matching_docs and matching_docs.get("ids")
            else 0
        )
    else:
        total_docs = collection.count()

    counts = {theme: 0 for theme in THEMES_LIST}
    if total_docs <= 0:
        return {
            "counts": counts,
            "percentages": percentages_from_counts(counts),
            "total_docs": 0,
        }

    theme_embeddings = get_theme_query_embeddings(model_id)
    best_by_doc = {}
    for theme_name in THEMES_LIST:
        results = collection.query(
            query_embeddings=[theme_embeddings[theme_name]],
            n_results=total_docs,
            where=where_filter,
            include=["distances"],
        )
        ids = results.get("ids", [[]])[0] if results.get("ids") else []
        distances = results.get("distances", [[]])[0] if results.get("distances") else []
        for doc_id, distance in zip(ids, distances):
            current = best_by_doc.get(doc_id)
            if current is None or distance < current[0]:
                best_by_doc[doc_id] = (distance, theme_name)

    for _, theme_name in best_by_doc.values():
        counts[theme_name] += 1

    return {
        "counts": counts,
        "percentages": percentages_from_counts(counts),
        "total_docs": total_docs,
    }


def collect_theme_documents(
    collection,
    theme_name: str,
    *,
    filters: dict | None = None,
    model_id: str | None = None,
) -> dict:
    """
    Collect the filtered documents whose nearest theme query is the requested theme.

    This intentionally does not bind responses to the survey question they came from.
    Each answer is compared against every theme definition and assigned to the closest
    theme in embedding space, so off-topic-but-useful student comments can move to the
    theme they actually discuss.
    """
    where_filter = build_where_filter(filters or {})
    if where_filter:
        matching_docs = collection.get(where=where_filter)
        total_docs = (
            len(matching_docs["ids"])
            if matching_docs and matching_docs.get("ids")
            else 0
        )
    else:
        total_docs = collection.count()

    counts = {theme: 0 for theme in THEMES_LIST}
    if total_docs <= 0:
        return {
            "frequency": 0,
            "vector_relevant_count": 0,
            "total_filtered_documents": 0,
            "documents": [],
            "metadatas": [],
            "distances": [],
            "counts": counts,
            "percentages": percentages_from_counts(counts),
        }

    selected_model = model_id or collection_embedding_model(collection)
    theme_embeddings = get_theme_query_embeddings(selected_model)
    best_by_doc = {}
    target_docs = {}

    for candidate_theme in THEMES_LIST:
        include = (
            ["documents", "metadatas", "distances"]
            if candidate_theme == theme_name
            else ["distances"]
        )
        results = collection.query(
            query_embeddings=[theme_embeddings[candidate_theme]],
            n_results=total_docs,
            where=where_filter,
            include=include,
        )
        ids = results.get("ids", [[]])[0] if results.get("ids") else []
        distances = results.get("distances", [[]])[0] if results.get("distances") else []

        if candidate_theme == theme_name:
            documents = results.get("documents", [[]])[0] if results.get("documents") else []
            metadatas = (
                results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            )
            if len(metadatas) < len(documents):
                metadatas = list(metadatas) + [{} for _ in range(len(documents) - len(metadatas))]
            for doc_id, doc, meta, distance in zip(ids, documents, metadatas, distances):
                target_docs[doc_id] = {
                    "document": doc,
                    "metadata": meta,
                    "distance": distance,
                }

        for doc_id, distance in zip(ids, distances):
            current = best_by_doc.get(doc_id)
            if current is None or distance < current[0]:
                best_by_doc[doc_id] = (distance, candidate_theme)

    selected_rows = []
    for doc_id, (distance, assigned_theme) in best_by_doc.items():
        counts[assigned_theme] += 1
        if assigned_theme == theme_name and doc_id in target_docs:
            row = dict(target_docs[doc_id])
            row["distance"] = distance
            selected_rows.append(row)

    selected_rows.sort(key=lambda row: row["distance"])
    percentages = percentages_from_counts(counts)
    return {
        "frequency": percentages.get(theme_name, 0),
        "vector_relevant_count": counts.get(theme_name, 0),
        "total_filtered_documents": total_docs,
        "documents": [row["document"] for row in selected_rows],
        "metadatas": [row["metadata"] for row in selected_rows],
        "distances": [row["distance"] for row in selected_rows],
        "counts": counts,
        "percentages": percentages,
    }


def filtered_themes_overview(cache: dict, filters: dict) -> dict:
    if not filters:
        return cache

    cache_key = theme_overview_cache_key(filters)
    if cache_key in _theme_overview_cache:
        return _theme_overview_cache[cache_key]

    collection = get_collection()
    where_clause = build_where_filter(filters)
    filtered_docs = collection.get(where=where_clause)
    total_docs = len(filtered_docs["ids"]) if filtered_docs and filtered_docs["ids"] else 0

    import copy

    new_cache = copy.deepcopy(cache)
    if total_docs == 0:
        for theme in new_cache:
            new_cache[theme]["frequency"] = 0
        _theme_overview_cache[cache_key] = new_cache
        return new_cache

    distribution = theme_distribution(
        collection,
        collection_embedding_model(collection),
        where_filter=where_clause,
    )
    for theme_name in THEMES_LIST:
        if theme_name not in new_cache:
            continue
        new_cache[theme_name]["frequency"] = distribution["percentages"].get(theme_name, 0)
        new_cache[theme_name]["vector_relevant_count"] = distribution["counts"].get(
            theme_name, 0
        )

    _theme_overview_cache[cache_key] = new_cache
    return new_cache
