from importlib import import_module
import json
import os

from src.config.paths import ANONYMIZED_CSV_PATH, VECTOR_DB_PATH
from .embedding_models import DEFAULT_EMBEDDING_MODEL

_builder = import_module("src.pipeline.02_embedding.vector_builder")


def build_vectors_stream(
    *,
    embedding_model: str | None,
    selected_columns: list | None,
    allow_model_download: bool,
):
    if not ANONYMIZED_CSV_PATH.exists():
        raise FileNotFoundError("Anonymized CSV not found")

    selected_model = str(embedding_model or DEFAULT_EMBEDDING_MODEL).strip()
    print(
        f"[BUILD-VECTORS] Starting vector DB build with model={selected_model}, "
        f"columns={selected_columns}, allow_model_download={allow_model_download}"
    )

    return _builder.build_vector_db_stream(
        csv_path=str(ANONYMIZED_CSV_PATH),
        db_path=str(VECTOR_DB_PATH),
        embedding_model=selected_model,
        selected_columns=selected_columns,
        allow_model_download=allow_model_download,
    )


def rerank_theme_assignments_stream(
    *,
    reranker_model: str | None,
    allow_model_download: bool,
    max_documents: int | None = None,
):
    print(
        f"[RERANK-THEMES] Starting post-embedding rerank with "
        f"model={reranker_model or 'configured default'}, "
        f"allow_model_download={allow_model_download}, "
        f"max_documents={max_documents}"
    )
    return _builder.apply_theme_reranker_stream(
        db_path=str(VECTOR_DB_PATH),
        reranker_model_id=reranker_model,
        allow_model_download=allow_model_download,
        max_documents=max_documents,
    )


def vector_checkpoint_status_payload() -> dict:
    if not _builder.VECTOR_CHECKPOINT.exists():
        return {"has_checkpoint": False}
    try:
        meta = json.loads(_builder.VECTOR_CHECKPOINT.read_text(encoding="utf-8"))
        return {
            "has_checkpoint": True,
            "processed_count": meta.get("processed_count", 0),
            "total_docs": meta.get("total_docs", 0),
            "embedding_model": meta.get("embedding_model"),
            "selected_columns": meta.get("selected_columns", []),
        }
    except Exception:
        return {"has_checkpoint": False}


def pipeline_status_payload() -> dict:
    vector_db_storage_exists = VECTOR_DB_PATH.exists() and any(
        os.scandir(VECTOR_DB_PATH)
    )
    vector_db_ready = (
        vector_db_storage_exists
        and _builder.vector_db_is_ready(str(VECTOR_DB_PATH))
    )
    vector_metadata = {}
    if vector_db_ready:
        try:
            import chromadb

            collection = chromadb.PersistentClient(
                path=str(VECTOR_DB_PATH)
            ).get_collection("survey_responses")
            vector_metadata = getattr(collection, "metadata", None) or {}
        except Exception:
            vector_metadata = {}
    return {
        "status": "success",
        "anonymized_exists": ANONYMIZED_CSV_PATH.exists(),
        "vector_db_exists": vector_db_ready,
        "vector_db_storage_exists": vector_db_storage_exists,
        "vector_db_ready": vector_db_ready,
        "theme_reranker_status": vector_metadata.get("theme_reranker_status"),
        "theme_reranker_model": vector_metadata.get("theme_reranker_model"),
        "theme_embedding_confidence_margin": vector_metadata.get(
            "theme_embedding_confidence_margin"
        ),
    }
