import pandas as pd
import chromadb
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json
from importlib import import_module

from src.config.paths import CACHE_FILE, VECTOR_CHECKPOINT
from src.config.response_quality import (
    LOW_INFORMATION_VALUE,
    RESPONSE_QUALITY_METADATA_KEY,
    RESPONSE_QUALITY_VERSION,
    response_quality,
)
from src.config.themes import (
    LOW_INFORMATION_THEME,
    METADATA_COLS,
    SOURCE_METADATA_ALIASES,
    THEME_EMBEDDING_DEFINITIONS,
)
from .embedding_models import (
    AVAILABLE_EMBEDDING_MODELS,
    DEFAULT_EMBEDDING_MODEL,
    describe_embedding_runtime,
    load_embedding_model,
    unload_embedding_models,
)
from .theme_classifier import (
    CLASSIFICATION_STATUS_BUILDING,
    CLASSIFICATION_STATUS_READY,
    ThemeClassificationConfig,
    classification_config,
    classify_theme_batch,
    encode_theme_definitions,
)
from src.utils.model_device import describe_model_device, get_model_device
from src.utils.file_parsers import detect_sep, is_questionnaire_column

reranker_models = import_module("src.pipeline.03_retrieval.reranker_models")

VECTOR_SCHEMA_VERSION = 3


def _load_vector_checkpoint(
    csv_path: str,
    embedding_model: str,
    selected_columns: list,
    db_path: str,
    classification: ThemeClassificationConfig,
) -> int:
    """Return processed_count if a valid checkpoint exists for the same run, else 0."""
    if not VECTOR_CHECKPOINT.exists():
        return 0
    try:
        stat = os.stat(csv_path)
        meta = json.loads(VECTOR_CHECKPOINT.read_text(encoding="utf-8"))
        if meta.get("csv_size") != stat.st_size:
            return 0
        if abs(meta.get("csv_mtime", 0) - stat.st_mtime) > 2:
            return 0
        if meta.get("embedding_model") != embedding_model:
            return 0
        if meta.get("selected_columns") != selected_columns:
            return 0
        if meta.get("vector_schema_version") != VECTOR_SCHEMA_VERSION:
            return 0
        for key, value in classification.collection_metadata(
            status=CLASSIFICATION_STATUS_BUILDING
        ).items():
            if meta.get(key) != value:
                return 0
        try:
            collection = chromadb.PersistentClient(path=str(db_path)).get_collection(
                "survey_responses"
            )
            collection_metadata = getattr(collection, "metadata", None) or {}
            for key, value in classification.collection_metadata(
                status=CLASSIFICATION_STATUS_BUILDING
            ).items():
                if collection_metadata.get(key) != value:
                    return 0
            processed_count = int(meta.get("processed_count", 0))
            if processed_count < 0 or collection.count() < processed_count:
                return 0
        except Exception:
            return 0
        return processed_count
    except Exception:
        return 0


def _save_vector_checkpoint(meta: dict):
    try:
        VECTOR_CHECKPOINT.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[VECTOR CHECKPOINT] Warning: could not save: {e}")


def _clear_vector_checkpoint():
    try:
        if VECTOR_CHECKPOINT.exists():
            VECTOR_CHECKPOINT.unlink()
    except Exception:
        pass


def _collection_metadata(
    embedding_model: str,
    classification: ThemeClassificationConfig,
    *,
    status: str,
    include_hnsw_space: bool = True,
) -> dict:
    metadata = {
        "embedding_model": embedding_model,
        "vector_schema_version": VECTOR_SCHEMA_VERSION,
        "response_quality_version": RESPONSE_QUALITY_VERSION,
        **classification.collection_metadata(status=status),
    }
    if include_hnsw_space:
        metadata["hnsw:space"] = "cosine"
    return metadata


def _invalidate_insight_cache() -> None:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    try:
        retrieval = import_module("src.pipeline.03_retrieval.service")
        retrieval.clear_runtime_caches()
    except Exception:
        pass


def _validate_classified_collection(
    collection,
    *,
    expected_count: int,
    classification: ThemeClassificationConfig,
) -> None:
    stored = collection.get(include=["metadatas"])
    ids = stored.get("ids") or []
    metadatas = stored.get("metadatas") or []
    if len(ids) != expected_count or len(metadatas) != expected_count:
        raise RuntimeError(
            "Vector build is incomplete: stored document count does not match "
            "the classified source document count."
        )
    for doc_id, metadata in zip(ids, metadatas):
        metadata = metadata or {}
        primary_theme = metadata.get("theme_primary")
        expected_candidates = (
            1
            if primary_theme == LOW_INFORMATION_THEME
            else classification.candidate_count
        )
        if (
            metadata.get("theme_classification_version")
            != classification.classification_version
            or metadata.get("theme_taxonomy_version")
            != classification.taxonomy_version
            or metadata.get("theme_embedding_model")
            != classification.embedding_model_id
            or metadata.get("theme_reranker_model")
            != classification.reranker_model_id
            or metadata.get("theme_ambiguity_score_margin")
            != classification.ambiguity_score_margin
            or metadata.get("theme_candidate_count") != expected_candidates
            or not primary_theme
        ):
            raise RuntimeError(
                f"Vector build is incomplete: document {doc_id} is missing a "
                "compatible persisted theme assignment."
            )
        for position in range(1, expected_candidates + 1):
            if not metadata.get(f"theme_candidate_{position}"):
                raise RuntimeError(
                    f"Vector build is incomplete: document {doc_id} is missing "
                    f"persisted candidate theme {position}."
                )


def _load_reranker_for_classification(
    classification: ThemeClassificationConfig,
    *,
    allow_model_download: bool,
):
    if classification.reranker_model_id == "disabled":
        return None
    return reranker_models.load_reranker_model(
        classification.reranker_model_id,
        allow_download=allow_model_download,
    )


def _classification_for_embedding_model(
    embedding_model: str,
) -> ThemeClassificationConfig:
    reranker_model_id = (
        reranker_models.selected_reranker_model()
        if reranker_models.reranker_enabled()
        else None
    )
    return classification_config(
        embedding_model,
        reranker_model_id=reranker_model_id,
    )


def vector_db_is_ready(db_path: str) -> bool:
    try:
        collection = chromadb.PersistentClient(path=str(db_path)).get_collection(
            "survey_responses"
        )
        metadata = getattr(collection, "metadata", None) or {}
        embedding_model = metadata.get("embedding_model")
        if not embedding_model:
            return False
        expected = _classification_for_embedding_model(embedding_model)
        return all(
            metadata.get(key) == value
            for key, value in expected.collection_metadata(
                status=CLASSIFICATION_STATUS_READY
            ).items()
        )
    except Exception:
        return False


METADATA_ALIASES = SOURCE_METADATA_ALIASES


def _first_metadata_value(row, aliases):
    for col in aliases:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col])
    return None


def build_metadata(row) -> dict:
    meta = {
        "question": str(row.get("question", "N/A")),
        RESPONSE_QUALITY_METADATA_KEY: response_quality(row.get("answer", "")),
    }
    for canonical_key, aliases in METADATA_ALIASES.items():
        value = _first_metadata_value(row, aliases)
        if value:
            meta[canonical_key] = value

    # Keep the original metadata too for debugging/backwards compatibility,
    # but the dashboard should use the canonical keys above.
    for col in METADATA_COLS:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            meta[col.lower()] = str(row[col])
    return meta


def build_vector_db(csv_path="data/anonymized_output.csv", db_path="./survey_vector_db"):
    if not os.path.exists(csv_path):
        raise Exception(f"Input file {csv_path} not found. Please anonymize first.")

    # 1. Config 
    CSV_SEP = detect_sep(csv_path)
    df_temp = pd.read_csv(csv_path, sep=CSV_SEP, nrows=1, encoding='utf-8-sig')
    ANSWER_COLS = [col for col in df_temp.columns if is_questionnaire_column(col)]
    COLLECTION = 'survey_responses'
    EMBEDDING_MODEL = DEFAULT_EMBEDDING_MODEL
    BATCH_SIZE = 64
    if EMBEDDING_MODEL not in AVAILABLE_EMBEDDING_MODELS:
        raise Exception(f"Unsupported embedding model: {EMBEDDING_MODEL}")

    # 2. Load
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path, sep=CSV_SEP, encoding='utf-8-sig')

    # Combine answers
    all_records = []
    for question_col in ANSWER_COLS:
        if question_col in df.columns:
            temp_df = df[df[question_col].notna()].copy()
            temp_df['question'] = question_col
            temp_df['answer'] = temp_df[question_col].astype(str)
            all_records.append(temp_df)
    
    if not all_records:
        raise Exception("No matching answer columns found in the dataset.")
        
    df_combined = pd.concat(all_records, ignore_index=True)

    classification = _classification_for_embedding_model(EMBEDDING_MODEL)
    print(f"Generating embeddings and theme assignments for {len(df_combined)} rows...")
    device = get_model_device()
    print(f"Loading embedding model on {describe_model_device(device)}...")
    model = load_embedding_model(EMBEDDING_MODEL)
    reranker_model = None
    try:
        if classification.reranker_model_id != "disabled":
            print(f"Loading reranker {classification.reranker_model_id}...")
        reranker_model = _load_reranker_for_classification(
            classification,
            allow_model_download=True,
        )
        theme_names, theme_embeddings = encode_theme_definitions(model)

        print(f"Writing to ChromaDB at '{db_path}'...")
        client = chromadb.PersistentClient(path=db_path)

        try:
            client.delete_collection(COLLECTION)
        except:
            pass

        collection = client.create_collection(
            name=COLLECTION,
            metadata=_collection_metadata(
                EMBEDDING_MODEL,
                classification,
                status=CLASSIFICATION_STATUS_BUILDING,
            ),
        )
        _invalidate_insight_cache()

        for start in range(0, len(df_combined), BATCH_SIZE):
            end = min(start + BATCH_SIZE, len(df_combined))
            batch = df_combined.iloc[start:end]
            batch_docs = batch["answer"].tolist()
            batch_embeddings = model.encode(
                batch_docs,
                batch_size=BATCH_SIZE,
                normalize_embeddings=True,
            )
            assignments = classify_theme_batch(
                batch_docs,
                batch_embeddings,
                theme_names=theme_names,
                theme_embeddings=theme_embeddings,
                config=classification,
                reranker_model=reranker_model,
            )
            batch_metadata = []
            for (_, row), assignment in zip(batch.iterrows(), assignments):
                batch_metadata.append({**build_metadata(row), **assignment})

            collection.upsert(
                ids=[f"doc_{i}" for i in range(start, end)],
                embeddings=batch_embeddings.tolist(),
                documents=batch_docs,
                metadatas=batch_metadata,
            )

        _validate_classified_collection(
            collection,
            expected_count=len(df_combined),
            classification=classification,
        )
        collection.modify(
            metadata=_collection_metadata(
                EMBEDDING_MODEL,
                classification,
                status=CLASSIFICATION_STATUS_READY,
                include_hnsw_space=False,
            )
        )
        low_information_count = sum(
            response_quality(answer) == LOW_INFORMATION_VALUE
            for answer in df_combined["answer"]
        )
        return {
            "status": "success",
            "rows_embedded": len(df_combined),
            "low_information_responses": low_information_count,
        }
    finally:
        model = None
        reranker_model = None
        unload_embedding_models()
        reranker_models.unload_reranker_models()

def build_vector_db_stream(
    csv_path="data/anonymized_survey.csv",
    db_path="./survey_vector_db",
    embedding_model=None,
    selected_columns=None,
    allow_model_download=True,
):
    if not os.path.exists(csv_path):
        yield json.dumps({"status": "error", "error": f"Input file {csv_path} not found. Please anonymize first."}) + "\n"
        return

    model = None
    reranker_model = None
    try:
        CSV_SEP = detect_sep(csv_path)
        COLLECTION = 'survey_responses'
        EMBEDDING_MODEL = str(embedding_model or DEFAULT_EMBEDDING_MODEL).strip()
        classification = _classification_for_embedding_model(EMBEDDING_MODEL)
        BATCH_SIZE = 100
        if EMBEDDING_MODEL not in AVAILABLE_EMBEDDING_MODELS:
            supported = ", ".join(AVAILABLE_EMBEDDING_MODELS)
            yield json.dumps({
                "status": "error",
                "error": f"Unsupported embedding model '{EMBEDDING_MODEL}'. Choose one of: {supported}.",
            }) + "\n"
            return

        # Load CSV
        yield json.dumps({"status": "progress", "message": f"Loading CSV from {csv_path}...", "progress": 10}) + "\n"
        df = pd.read_csv(csv_path, sep=CSV_SEP, encoding='utf-8-sig')

        if selected_columns and len(selected_columns) > 0:
            ANSWER_COLS = [col for col in selected_columns if col in df.columns]
            yield json.dumps({"status": "progress", "message": f"Using {len(ANSWER_COLS)} selected columns: {', '.join(ANSWER_COLS)}", "progress": 12}) + "\n"
        else:
            ANSWER_COLS = [col for col in df.columns if is_questionnaire_column(col)]

        if not ANSWER_COLS:
            yield json.dumps({"status": "error", "error": "No matching columns found in the dataset."}) + "\n"
            return

        all_records = []
        for question_col in ANSWER_COLS:
            if question_col in df.columns:
                temp_df = df[df[question_col].notna()].copy()
                temp_df['question'] = question_col
                temp_df['answer'] = temp_df[question_col].astype(str)
                all_records.append(temp_df)

        if not all_records:
            yield json.dumps({"status": "error", "error": "No matching answer columns found in the dataset."}) + "\n"
            return

        df_combined = pd.concat(all_records, ignore_index=True)
        total_docs = len(df_combined)

        # Check for a resumable checkpoint.
        resume_from = _load_vector_checkpoint(
            csv_path,
            EMBEDDING_MODEL,
            ANSWER_COLS,
            db_path,
            classification,
        )
        is_resuming = resume_from > 0

        if is_resuming:
            yield json.dumps({
                "status": "progress",
                "message": f"Resuming from checkpoint — {resume_from}/{total_docs} documents already indexed...",
                "progress": 15,
            }) + "\n"

        # Load/validate the model before touching ChromaDB.
        yield json.dumps({"status": "progress", "message": f"Loading {EMBEDDING_MODEL} embedding model via {describe_embedding_runtime(EMBEDDING_MODEL)}...", "progress": 25}) + "\n"
        try:
            model = load_embedding_model(EMBEDDING_MODEL, allow_download=allow_model_download)
        except Exception as e:
            download_hint = (
                " Allow model download or choose a locally cached model."
                if not allow_model_download
                else " Check your internet connection, HF_TOKEN, or model name."
            )
            yield json.dumps({"status": "error", "error": f"Embedding model could not be loaded: {e}.{download_hint}"}) + "\n"
            return

        if classification.reranker_model_id == "disabled":
            yield json.dumps({
                "status": "progress",
                "message": "Reranker disabled; theme classification will use embedding cosine similarity fallback.",
                "progress": 27,
            }) + "\n"
        else:
            yield json.dumps({
                "status": "progress",
                "message": f"Loading {classification.reranker_model_id} reranker for batched theme classification...",
                "progress": 27,
            }) + "\n"
        try:
            reranker_model = _load_reranker_for_classification(
                classification,
                allow_model_download=allow_model_download,
            )
        except Exception as e:
            yield json.dumps({
                "status": "error",
                "error": f"Reranker model could not be loaded: {e}.",
            }) + "\n"
            return

        yield json.dumps({
            "status": "progress",
            "message": (
                f"Embedding {len(THEME_EMBEDDING_DEFINITIONS)} theme definitions; "
                f"top {classification.candidate_count} candidates per response will be reranked."
            ),
            "progress": 29,
        }) + "\n"
        theme_names, theme_embeddings = encode_theme_definitions(model)

        yield json.dumps({"status": "progress", "message": "Connecting to ChromaDB...", "progress": 30}) + "\n"
        client = chromadb.PersistentClient(path=str(db_path))

        if is_resuming:
            # Reuse the existing collection — do not delete it.
            collection = client.get_or_create_collection(
                COLLECTION,
                metadata=_collection_metadata(
                    EMBEDDING_MODEL,
                    classification,
                    status=CLASSIFICATION_STATUS_BUILDING,
                ),
            )
        else:
            try:
                client.delete_collection(COLLECTION)
            except Exception:
                pass
            collection = client.create_collection(
                COLLECTION,
                metadata=_collection_metadata(
                    EMBEDDING_MODEL,
                    classification,
                    status=CLASSIFICATION_STATUS_BUILDING,
                ),
            )
            _invalidate_insight_cache()

        yield json.dumps({"status": "progress", "message": f"Found {total_docs} documents to embed and classify. Starting batched indexing...", "progress": 40}) + "\n"

        stat = os.stat(csv_path)
        checkpoint_meta = {
            "csv_size": stat.st_size,
            "csv_mtime": stat.st_mtime,
            "embedding_model": EMBEDDING_MODEL,
            "selected_columns": ANSWER_COLS,
            "total_docs": total_docs,
            "processed_count": resume_from,
            "vector_schema_version": VECTOR_SCHEMA_VERSION,
            **classification.collection_metadata(
                status=CLASSIFICATION_STATUS_BUILDING
            ),
        }

        processed_count = resume_from

        for start in range(resume_from, total_docs, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_docs)

            batch = df_combined.iloc[start:end]
            batch_docs = batch['answer'].tolist()
            # Deterministic IDs so resume can safely skip already-indexed batches.
            batch_ids = [f"doc_{start + j}" for j in range(len(batch))]
            batch_meta = [build_metadata(row) for _, row in batch.iterrows()]

            batch_embeddings = model.encode(batch_docs, normalize_embeddings=True)
            assignments = classify_theme_batch(
                batch_docs,
                batch_embeddings,
                theme_names=theme_names,
                theme_embeddings=theme_embeddings,
                config=classification,
                reranker_model=reranker_model,
            )
            batch_meta = [
                {**metadata, **assignment}
                for metadata, assignment in zip(batch_meta, assignments)
            ]

            collection.upsert(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
                embeddings=batch_embeddings.tolist()
            )

            processed_count = end
            checkpoint_meta["processed_count"] = processed_count
            _save_vector_checkpoint(checkpoint_meta)

            progress = 40 + int(55 * (processed_count / total_docs))
            yield json.dumps({
                "status": "progress",
                "message": f"Embedded, classified, and indexed {processed_count}/{total_docs} documents...",
                "progress": progress,
                "current_doc": str(batch_docs[-1])[:100] + "..." if batch_docs else "",
                "checkpoint_saved": True,
            }) + "\n"

        yield json.dumps({
            "status": "progress",
            "message": "Validating persisted theme assignments before marking the database ready...",
            "progress": 96,
        }) + "\n"
        _validate_classified_collection(
            collection,
            expected_count=total_docs,
            classification=classification,
        )
        collection.modify(
            metadata=_collection_metadata(
                EMBEDDING_MODEL,
                classification,
                status=CLASSIFICATION_STATUS_READY,
                include_hnsw_space=False,
            )
        )
        _clear_vector_checkpoint()

        low_information_count = sum(
            response_quality(answer) == LOW_INFORMATION_VALUE
            for answer in df_combined["answer"]
        )
        yield json.dumps({
            "status": "success",
            "message": "Vector DB built successfully",
            "document_count": total_docs,
            "vectors_created": total_docs,
            "theme_classification_version": classification.classification_version,
            "theme_candidate_count": classification.candidate_count,
            "theme_reranker_model": classification.reranker_model_id,
            "theme_ambiguity_score_margin": classification.ambiguity_score_margin,
            "low_information_responses": low_information_count,
            "progress": 100
        }) + "\n"

    except Exception as e:
        yield json.dumps({"status": "error", "error": str(e)}) + "\n"
    finally:
        if model is not None:
            model = None
        reranker_model = None
        unload_embedding_models()
        reranker_models.unload_reranker_models()
