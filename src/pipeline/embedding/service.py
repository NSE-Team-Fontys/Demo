from importlib import import_module
import json
import os

from src.config.paths import ANONYMIZED_CSV_PATH, VECTOR_DB_PATH
from src.pipeline.embedding.embedding_models import DEFAULT_EMBEDDING_MODEL

_builder = import_module("src.pipeline.embedding.vector_builder")


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
    vector_db_exists = VECTOR_DB_PATH.exists() and any(os.scandir(VECTOR_DB_PATH))
    return {
        "status": "success",
        "anonymized_exists": ANONYMIZED_CSV_PATH.exists(),
        "vector_db_exists": vector_db_exists,
    }
