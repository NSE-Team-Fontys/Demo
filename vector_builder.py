import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json
import csv

from src.core.model_device import describe_model_device, get_model_device


METADATA_COLS = {
    'ID',
    'Institution',
    'academic_year',
    'location',
    'programme',
    'study_mode',
    'cohort',
    'Jaar',
    'Actuele BRIN-code volgens RIO',
    'Actuele naam instelling volgens RIO',
    'Actuele CROHO-code volgens RIO',
    'Actuele Opleidingsnaam volgens RIO',
    'Actuele BRIN-volgnummer volgens RIO',
    'Type Student',
    'Opleidingsvorm (vt dt du)',
    'Leerroute_Track',
    'Studiejaar volgens instelling',
    'Kunstopleiding',
    'Afstandsonderwijs',
}

METADATA_ALIASES = {
    'institution': [
        'Institution',
        'Actuele naam instelling volgens RIO',
    ],
    'academic_year': [
        'academic_year',
        'Jaar',
    ],
    'location': [
        'location',
    ],
    # For the NSE/RIO export, the useful dashboard programme filter is the track
    # (e.g. Software Engineering/Data Science), not the broad HBO-ICT CROHO name.
    'programme': [
        'programme',
        'Leerroute_Track',
        'Actuele Opleidingsnaam volgens RIO',
    ],
    'study_mode': [
        'study_mode',
        'Type Student',
        'Opleidingsvorm (vt dt du)',
    ],
    'cohort': [
        'cohort',
        'Studiejaar volgens instelling',
    ],
}


def detect_sep(path: str) -> str:
    candidates = [',', ';', '\t']
    try:
        with open(path, 'r', encoding='utf-8-sig', errors='ignore', newline='') as f:
            lines = []
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                if line.strip():
                    lines.append(line)
        if not lines:
            return ';'

        sample = ''.join(lines)
        try:
            sniffed = csv.Sniffer().sniff(sample, delimiters=''.join(candidates)).delimiter
            if sniffed in candidates:
                return sniffed
        except Exception:
            pass

        def score(delim: str):
            counts = []
            bad = 0
            for ln in lines:
                try:
                    row = next(csv.reader([ln], delimiter=delim, quotechar='"', escapechar='\\'))
                    counts.append(len(row))
                except Exception:
                    bad += 1
            if not counts:
                return (0, -10_000, -1_000 - bad)
            mode = max(set(counts), key=counts.count)
            var = sum(abs(c - mode) for c in counts)
            return (mode, -var, -bad)

        return max(candidates, key=score)
    except Exception:
        return ';'


def is_questionnaire_column(col: str) -> bool:
    name = str(col).strip()
    lower = name.lower()
    if name in METADATA_COLS or lower.startswith('themascore'):
        return False
    return (
        '?' in name
        or lower.startswith('wil jij')
        or lower.startswith('waarom')
        or lower.startswith('wat voor soort')
    )


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


def load_embedding_model(model_id: str, allow_download: bool = True) -> SentenceTransformer:
    """
    Load the embedding model before touching ChromaDB.
    If allow_download=False, only already-cached/local models are accepted.
    """
    device = get_model_device()
    try:
        return SentenceTransformer(
            model_id,
            model_kwargs={'use_safetensors': True},
            local_files_only=not allow_download,
            device=device,
        )
    except TypeError:
        # Older sentence-transformers versions may not support local_files_only.
        if not allow_download:
            raise RuntimeError(
                "Cannot verify local-only model availability with this sentence-transformers version. "
                "Enable model downloads or update sentence-transformers."
            )
        return SentenceTransformer(model_id, model_kwargs={'use_safetensors': True}, device=device)


def build_vector_db(csv_path="data/anonymized_output.csv", db_path="./survey_vector_db"):
    if not os.path.exists(csv_path):
        raise Exception(f"Input file {csv_path} not found. Please anonymize first.")

    # 1. Config 
    CSV_SEP = detect_sep(csv_path)
    df_temp = pd.read_csv(csv_path, sep=CSV_SEP, nrows=1, encoding='utf-8-sig')
    ANSWER_COLS = [col for col in df_temp.columns if is_questionnaire_column(col)]
    COLLECTION = 'survey_responses'
    EMBEDDING_MODEL = 'BAAI/bge-m3'
    BATCH_SIZE = 64

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
    model = SentenceTransformer(
        EMBEDDING_MODEL,
        model_kwargs={'use_safetensors': True},
        device=device,
    )
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

    collection = client.create_collection(name=COLLECTION, metadata={"hnsw:space": "cosine"})

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
    
    try:
        CSV_SEP = detect_sep(csv_path)
        COLLECTION = 'survey_responses'
        EMBEDDING_MODEL = embedding_model or 'BAAI/bge-m3'
        BATCH_SIZE = 50

        # Load CSV
        yield json.dumps({"status": "progress", "message": f"Loading CSV from {csv_path}...", "progress": 10}) + "\n"
        df = pd.read_csv(csv_path, sep=CSV_SEP, encoding='utf-8-sig')

        # Use selected columns if provided, otherwise auto-detect questionnaire columns
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

        # Load/validate the model before touching ChromaDB, so failures do not
        # destroy the old vector database.
        device = get_model_device()
        yield json.dumps({"status": "progress", "message": f"Loading {EMBEDDING_MODEL} embedding model on {describe_model_device(device)}...", "progress": 25}) + "\n"
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

        # Initialize client only after model preflight succeeds.
        yield json.dumps({"status": "progress", "message": "Connecting to ChromaDB...", "progress": 30}) + "\n"
        client = chromadb.PersistentClient(path=str(db_path))

        try:
            client.delete_collection(COLLECTION)
        except:
            pass

        collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        
        total_docs = len(df_combined)
        yield json.dumps({"status": "progress", "message": f"Found {total_docs} documents to embed. Starting encoding...", "progress": 40}) + "\n"
        
        processed_count = 0
        
        import uuid

        for start in range(0, total_docs, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_docs)
            batch = df_combined.iloc[start:end]
            
            batch_docs = batch['answer'].tolist()
            batch_ids = [str(uuid.uuid4()) for _ in range(len(batch))]
            
            batch_meta = [build_metadata(row) for _, row in batch.iterrows()]
            
            # Encode batch
            batch_embeddings = model.encode(batch_docs, normalize_embeddings=True)
            
            # Add to collection
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
                embeddings=batch_embeddings.tolist()
            )
            
            processed_count += len(batch_ids)
            progress = 40 + int(55 * (processed_count / total_docs))
            
            yield json.dumps({
                "status": "progress", 
                "message": f"Embedded and indexed {processed_count}/{total_docs} documents...",
                "progress": progress,
                "current_doc": str(batch_docs[-1])[:100] + "..." if batch_docs else ""
            }) + "\n"

        yield json.dumps({
            "status": "success", 
            "message": "Vector DB built successfully",
            "document_count": total_docs,
            "vectors_created": total_docs,
            "progress": 100
        }) + "\n"
        
    except Exception as e:
        yield json.dumps({"status": "error", "error": str(e)}) + "\n"
