import pandas as pd
import chromadb
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json

from src.config.paths import VECTOR_CHECKPOINT
from src.config.themes import METADATA_COLS, SOURCE_METADATA_ALIASES
from .embedding_models import (
    AVAILABLE_EMBEDDING_MODELS,
    DEFAULT_EMBEDDING_MODEL,
    describe_embedding_runtime,
    load_embedding_model,
    unload_embedding_models,
)
from src.utils.model_device import describe_model_device, get_model_device
from src.utils.file_parsers import detect_sep, is_questionnaire_column


def _load_vector_checkpoint(csv_path: str, embedding_model: str, selected_columns: list, db_path: str) -> int:
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
        # Verify the ChromaDB collection still exists.
        try:
            chromadb.PersistentClient(path=str(db_path)).get_collection("survey_responses")
        except Exception:
            return 0
        return meta.get("processed_count", 0)
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


METADATA_ALIASES = SOURCE_METADATA_ALIASES


def _first_metadata_value(row, aliases):
    for col in aliases:
        if col in row and pd.notna(row[col]) and str(row[col]).strip():
            return str(row[col])
    return None


def build_metadata(row) -> dict:
    meta = {"question": str(row.get("question", "N/A"))}
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
            temp_df['answer'] = temp_df[question_col]
            all_records.append(temp_df)
    
    if not all_records:
        raise Exception("No matching answer columns found in the dataset.")
        
    df_combined = pd.concat(all_records, ignore_index=True)

    # 3. Embed
    print(f"Generating embeddings for {len(df_combined)} rows...")
    device = get_model_device()
    print(f"Loading embedding model on {describe_model_device(device)}...")
    model = load_embedding_model(EMBEDDING_MODEL)
    try:
        embeddings = model.encode(
            df_combined['answer'].tolist(),
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            normalize_embeddings=True
        )

        # 4. Store in ChromaDB
        print(f"Writing to ChromaDB at '{db_path}'...")
        client = chromadb.PersistentClient(path=db_path)

        try:
            client.delete_collection(COLLECTION)
        except:
            pass

        collection = client.create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL},
        )

        # Insert in batches
        for start in range(0, len(df_combined), BATCH_SIZE):
            end = min(start + BATCH_SIZE, len(df_combined))
            batch = df_combined.iloc[start:end]

            collection.add(
                ids=[f"id_{i}" for i in batch.index],
                embeddings=embeddings[start:end].tolist(),
                documents=batch['answer'].tolist(),
                metadatas=[{"question": str(row.get("question", "N/A"))} for _, row in batch.iterrows()]
            )

        return {"status": "success", "rows_embedded": len(df_combined)}
    finally:
        model = None
        unload_embedding_models()

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
    try:
        CSV_SEP = detect_sep(csv_path)
        COLLECTION = 'survey_responses'
        EMBEDDING_MODEL = str(embedding_model or DEFAULT_EMBEDDING_MODEL).strip()
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
                temp_df['answer'] = temp_df[question_col]
                all_records.append(temp_df)

        if not all_records:
            yield json.dumps({"status": "error", "error": "No matching answer columns found in the dataset."}) + "\n"
            return

        df_combined = pd.concat(all_records, ignore_index=True)
        total_docs = len(df_combined)

        # Check for a resumable checkpoint.
        resume_from = _load_vector_checkpoint(csv_path, EMBEDDING_MODEL, ANSWER_COLS, db_path)
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

        yield json.dumps({"status": "progress", "message": "Connecting to ChromaDB...", "progress": 30}) + "\n"
        client = chromadb.PersistentClient(path=str(db_path))

        if is_resuming:
            # Reuse the existing collection — do not delete it.
            collection = client.get_or_create_collection(
                COLLECTION,
                metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL},
            )
        else:
            try:
                client.delete_collection(COLLECTION)
            except Exception:
                pass
            collection = client.create_collection(
                COLLECTION,
                metadata={"hnsw:space": "cosine", "embedding_model": EMBEDDING_MODEL},
            )

        yield json.dumps({"status": "progress", "message": f"Found {total_docs} documents to embed. Starting encoding...", "progress": 40}) + "\n"

        stat = os.stat(csv_path)
        checkpoint_meta = {
            "csv_size": stat.st_size,
            "csv_mtime": stat.st_mtime,
            "embedding_model": EMBEDDING_MODEL,
            "selected_columns": ANSWER_COLS,
            "total_docs": total_docs,
            "processed_count": resume_from,
        }

        processed_count = resume_from

        for start in range(0, total_docs, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_docs)

            if end <= resume_from:
                # Already in ChromaDB — skip without re-encoding.
                continue

            batch = df_combined.iloc[start:end]
            batch_docs = batch['answer'].tolist()
            # Deterministic IDs so resume can safely skip already-indexed batches.
            batch_ids = [f"doc_{start + j}" for j in range(len(batch))]
            batch_meta = [build_metadata(row) for _, row in batch.iterrows()]

            batch_embeddings = model.encode(batch_docs, normalize_embeddings=True)

            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
                embeddings=batch_embeddings.tolist()
            )

            processed_count += len(batch_ids)
            checkpoint_meta["processed_count"] = processed_count
            _save_vector_checkpoint(checkpoint_meta)

            progress = 40 + int(55 * (processed_count / total_docs))
            yield json.dumps({
                "status": "progress",
                "message": f"Embedded and indexed {processed_count}/{total_docs} documents...",
                "progress": progress,
                "current_doc": str(batch_docs[-1])[:100] + "..." if batch_docs else "",
                "checkpoint_saved": True,
            }) + "\n"

        _clear_vector_checkpoint()

        yield json.dumps({
            "status": "success",
            "message": "Vector DB built successfully",
            "document_count": total_docs,
            "vectors_created": total_docs,
            "progress": 100
        }) + "\n"

    except Exception as e:
        yield json.dumps({"status": "error", "error": str(e)}) + "\n"
    finally:
        if model is not None:
            model = None
            unload_embedding_models()
