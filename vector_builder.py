import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import csv
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json


def detect_sep(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8-sig') as f:
            sample = f.read(8192)
        return csv.Sniffer().sniff(sample, delimiters=',;\t').delimiter
    except Exception:
        return ';'

def _is_texty(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if not isinstance(value, str):
        return False
    return bool(value.strip())

def pick_answer_columns(df: pd.DataFrame) -> list[str]:
    """
    Heuristic for selecting free-text answer columns across different CSV formats.
    Prefer columns containing 'feedback'. Fallback to columns that look like open text:
    - non-metadata
    - not score-only fields
    - enough non-empty strings / average length
    """
    cols = list(df.columns)
    feedback_cols = [c for c in cols if 'feedback' in str(c).lower()]
    if feedback_cols:
        return feedback_cols

    metadata_exact = {
        'id', 'institution', 'academic_year', 'location', 'programme', 'study_mode', 'cohort',
        'jaar', 'type student', 'opleidingsvorm (vt dt du)', 'leerroute_track',
        'studiejaar volgens instelling', 'kunstopopleiding', 'afstandsonderwijs',
    }

    def is_metadata_col(name: str) -> bool:
        n = str(name).strip().lower()
        if n in metadata_exact:
            return True
        # common institution/programme fields in Dutch exports
        # NOTE: "opleiding" also appears in open-question text, so keep this strict.
        if 'brin' in n or 'croho' in n:
            return True
        if n.startswith('actuele naam instelling') or n.startswith('actuele brin') or n.startswith('actuele croho'):
            return True
        if n.startswith('actuele opleidingsnaam') or n.startswith('actuele brin-volgnummer'):
            return True
        return False

    candidate_cols = []
    sample = df.head(min(len(df), 200))
    for c in cols:
        name = str(c)
        n = name.strip().lower()
        if is_metadata_col(name):
            continue
        if 'themascore' in n or 'score' in n:
            continue

        # compute textiness
        series = sample[c]
        non_empty = 0
        total_len = 0
        for v in series.tolist():
            if _is_texty(v):
                non_empty += 1
                total_len += len(v.strip())
        if non_empty == 0:
            continue
        avg_len = total_len / non_empty
        ratio = non_empty / max(len(series), 1)

        # accept likely open-text columns
        if ('?' in name) or ('wil jij' in n) or (avg_len >= 30 and ratio >= 0.05):
            candidate_cols.append(c)

    return candidate_cols

def build_vector_db(csv_path="data/anonymized_output.csv", db_path="./survey_vector_db"):
    if not os.path.exists(csv_path):
        raise Exception(f"Input file {csv_path} not found. Please anonymize first.")

    # 1. Config
    CSV_SEP = detect_sep(csv_path)
    df_temp = pd.read_csv(csv_path, sep=CSV_SEP, nrows=1)
    ANSWER_COLS = pick_answer_columns(df_temp)
    COLLECTION = 'survey_responses'
    EMBEDDING_MODEL = 'BAAI/bge-m3'
    BATCH_SIZE = 64

    # 2. Load
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path, sep=CSV_SEP)

    # In case nrows=1 didn't include representative text values
    if not ANSWER_COLS:
        ANSWER_COLS = pick_answer_columns(df)

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
    model = SentenceTransformer(EMBEDDING_MODEL)
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

def build_vector_db_stream(csv_path="data/anonymized_survey.csv", db_path="./survey_vector_db"):
    if not os.path.exists(csv_path):
        yield json.dumps({"status": "error", "error": f"Input file {csv_path} not found. Please anonymize first."}) + "\n"
        return
    
    try:
        CSV_SEP = detect_sep(csv_path)
        COLLECTION = 'survey_responses'
        EMBEDDING_MODEL = 'BAAI/bge-m3'
        BATCH_SIZE = 50

        # Load CSV
        yield json.dumps({"status": "progress", "message": f"Loading CSV from {csv_path}...", "progress": 10}) + "\n"
        df = pd.read_csv(csv_path, sep=CSV_SEP)

        # Dynamically find open-text columns across formats
        ANSWER_COLS = pick_answer_columns(df)
        
        if not ANSWER_COLS:
            yield json.dumps({
                "status": "error",
                "error": "No free-text columns found in the dataset. (Tried 'feedback' columns + fallback heuristic.)",
            }) + "\n"
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

        # Initialize client
        yield json.dumps({"status": "progress", "message": "Connecting to ChromaDB...", "progress": 15}) + "\n"
        client = chromadb.PersistentClient(path=str(db_path))
        
        try:
            client.delete_collection(COLLECTION)
        except:
            pass
            
        collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

        # Load model
        yield json.dumps({"status": "progress", "message": f"Loading {EMBEDDING_MODEL} embedding model...", "progress": 25}) + "\n"
        model = SentenceTransformer(EMBEDDING_MODEL)
        
        total_docs = len(df_combined)
        yield json.dumps({"status": "progress", "message": f"Found {total_docs} documents to embed. Starting encoding...", "progress": 40}) + "\n"
        
        processed_count = 0
        
        import uuid
        metadata_cols = [
            # canonical (your dashboard expects these lowercase keys)
            'Institution', 'academic_year', 'location', 'programme', 'study_mode', 'cohort', 'Jaar',
            # common Dutch export columns
            'Actuele naam instelling volgens RIO',
            'Actuele Opleidingsnaam volgens RIO',
            'Type Student',
            'Opleidingsvorm (vt dt du)',
            'Leerroute_Track',
            'Studiejaar volgens instelling',
        ]

        for start in range(0, total_docs, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_docs)
            batch = df_combined.iloc[start:end]
            
            batch_docs = batch['answer'].tolist()
            batch_ids = [str(uuid.uuid4()) for _ in range(len(batch))]
            
            batch_meta = []
            for _, row in batch.iterrows():
                meta = {"question": str(row.get("question", "N/A"))}
                for col in metadata_cols:
                    if col in row and pd.notna(row[col]) and str(row[col]).strip():
                        key = str(col).lower()
                        # normalize a few Dutch column names into dashboard keys
                        if key == 'jaar':
                            key = 'academic_year'
                        if key == 'actuele naam instelling volgens rio':
                            key = 'institution'
                        if key == 'actuele opleidingsnaam volgens rio':
                            key = 'programme'
                        if key == 'opleidingsvorm (vt dt du)':
                            key = 'study_mode'
                        meta[key] = str(row[col])
                batch_meta.append(meta)
            
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
