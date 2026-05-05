import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import json

def build_vector_db(csv_path="data/anonymized_output.csv", db_path="./survey_vector_db"):
    if not os.path.exists(csv_path):
        raise Exception(f"Input file {csv_path} not found. Please anonymize first.")

    # 1. Config 
    CSV_SEP = ';' 
    df_temp = pd.read_csv(csv_path, sep=CSV_SEP, nrows=1)
    ANSWER_COLS = [col for col in df_temp.columns if 'feedback' in col.lower()]
    COLLECTION = 'survey_responses'
    EMBEDDING_MODEL = 'BAAI/bge-m3'
    BATCH_SIZE = 64

    # 2. Load
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path, sep=CSV_SEP)

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
        CSV_SEP = ';' 
        COLLECTION = 'survey_responses'
        EMBEDDING_MODEL = 'BAAI/bge-m3'
        BATCH_SIZE = 50

        # Load CSV
        yield json.dumps({"status": "progress", "message": f"Loading CSV from {csv_path}...", "progress": 10}) + "\n"
        df = pd.read_csv(csv_path, sep=CSV_SEP)

        # Dynamically find all feedback columns
        ANSWER_COLS = [col for col in df.columns if 'feedback' in col.lower()]
        
        if not ANSWER_COLS:
            yield json.dumps({"status": "error", "error": "No feedback columns found in the dataset."}) + "\n"
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
        metadata_cols = ['Institution', 'academic_year', 'location', 'programme', 'study_mode', 'cohort']

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
                        meta[col.lower()] = str(row[col])
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
