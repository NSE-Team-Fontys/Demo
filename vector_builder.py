import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import os

def build_vector_db(csv_path="anonymized_output.csv", db_path="./survey_vector_db"):
    if not os.path.exists(csv_path):
        raise Exception(f"Input file {csv_path} not found. Please anonymize first.")

    # 1. Config 
    CSV_SEP = ';' 
    # Update these columns to match the actual feedback columns you want to embed
    ANSWER_COLS = [
        'Would you like to give your institution any other feedback on the teachers on your course programme?'
    ]
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