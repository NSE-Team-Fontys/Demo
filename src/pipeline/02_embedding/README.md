# Embedding Pipeline Module

This folder (`src/pipeline/embedding/`) contains the core components responsible for taking anonymized survey responses, converting them into vector embeddings, and indexing them in a vector database (ChromaDB) for subsequent retrieval and similarity search.

It is structured to be memory-efficient, resumable, and capable of streaming real-time progress to a web UI.

---

## Folder Structure

### 1. `embedding_models.py`
This module manages the instantiation and caching of the embedding models. 
- **Default Model:** `Octen/Octen-Embedding-0.6B`
- **Supported framework:** Uses `SentenceTransformer`.
- **Environment & Inference context:** Dynamically checks device availability (MPS/CUDA/CPU) via `src.utils.model_device` and respects environment variables like `HF_HUB_OFFLINE` to enforce offline execution using locally cached weights.
- It leverages an `lru_cache` to keep models in memory without multiple allocations across requests.

### 2. `vector_builder.py`
This is the workhorse of the embedding process. It takes the text from the `.csv` file, chunks/batches it, passes it through the embedding model, and persists the vectors into ChromaDB.
- **Batching & Streaming:** Defines a streaming generator function (`build_vector_db_stream`) that yields JSON strings, allowing an external caller (e.g., an API endpoint) to report real-time processing progress bars.
- **Checkpointing / Resumption:** Handles partial state mapping. It saves local checkpoint files containing metadata about how many documents have been successfully indexed. If a large indexing run is interrupted, it detects the checkpoint file, validates the CSV modification state, and resumes indexing exactly where it left off, avoiding redundant computation.
- **Metadata Management:** Extracts rich metadata (`build_metadata`) out of CSV rows (like question text and various aliases of demographic sources) and binds it to the vector payloads in ChromaDB for downstream filtering.
- **Cleanup:** Unloads models and explicitly clears PyTorch/MPS memory contexts upon completion to free up VRAM.

### 3. `service.py`
This module serves as the functional interface/facade between this pipeline package and HTTP API endpoints (found in `src/api/vector_routes.py` and analogous dashboard routes).
- **Triggers:** Wraps the initial vector building calls (e.g., `build_vectors_stream`).
- **Telemetry:** Exposes methods to evaluate the current status of the database and checkpoints (`vector_checkpoint_status_payload` and `pipeline_status_payload`).

---

## How it works (The Flow)

1. **Trigger:** The UI requests a vector build operation. `service.build_vectors_stream` is invoked.
2. **Analysis:** `vector_builder.py` loads the anonymized CSV, reads its schema, and identifies which columns are text responses based on headers and user-selected constraints.
3. **Model Load:** `embedding_models.py` conditionally downloads or loads a localized `SentenceTransformer` model onto the system GPU/MPS if available.
4. **Resumption check:** `vector_builder.py` reads local disk checkpoints. If you have already processed e.g. 5,000 of 10,000 respondents before a crash, it skips generating embeddings for the first 5,000.
5. **Embedding & Storage:** Iterating in batches (e.g., 50 records per batch), it encodes responses into float vectors, adds context metadata, and persists the payload into ChromaDB.
6. **Progress Streaming:** Every batch updates the client progress counter until vector building is 100% complete.
