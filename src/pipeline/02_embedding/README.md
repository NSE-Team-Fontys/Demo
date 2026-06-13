# Embedding Pipeline Module

This folder (`src/pipeline/embedding/`) contains the core components responsible for taking anonymized survey responses, converting them into vector embeddings, and indexing them in a vector database (ChromaDB) for subsequent retrieval and similarity search.

It is structured to be memory-efficient, resumable, and capable of streaming real-time progress to a web UI.

---

## Folder Structure

### 1. `embedding_models.py`
This module manages the instantiation and caching of the embedding models. 
- **Default Model:** `Octen/Octen-Embedding-0.6B`
- **Supported framework:** Uses `SentenceTransformer`.
- **Environment & Inference context:** Dynamically checks device availability (MPS/NVIDIA CUDA/AMD ROCm/CPU) via `src.utils.model_device` and respects environment variables like `HF_HUB_OFFLINE` to enforce offline execution using locally cached weights.
- It leverages an `lru_cache` to keep models in memory without multiple allocations across requests.

### 2. `vector_builder.py`
This is the workhorse of the embedding process. It takes the text from the `.csv` file, chunks/batches it, passes it through the embedding model, and persists the vectors into ChromaDB.
- **Batching & Streaming:** Defines a streaming generator function (`build_vector_db_stream`) that yields JSON strings, allowing an external caller (e.g., an API endpoint) to report real-time processing progress bars.
- **Checkpointing / Resumption:** Saves versioned checkpoint metadata and uses deterministic document IDs plus Chroma upserts. Replaying a partially committed batch cannot duplicate assignments.
- **Metadata Management:** Stores dashboard metadata and scalar theme-classification fields directly on each Chroma document. Candidate fields are queryable without modifying Chroma's internal SQLite schema.
- **Response Quality:** Labels conservative Dutch, English, and German filler responses such as `geen opmerkingen`, `no comment`, and `kein Kommentar` as `low_information` metadata. Retrieval reserves these responses for the `No Meaningful Response` sink theme.
- **Cleanup:** Unloads both embedding and cross-encoder models and clears accelerator memory after indexing.

### 3. `theme_classifier.py`
Classifies responses while their embeddings are already in memory:
- Embedding cosine similarity selects the configured top candidate themes.
- One batched cross-encoder call scores `(theme definition, response)` pairs.
- The highest raw reranker score selects the primary theme. These model-specific scores are not probabilities.
- A configurable top-two score margin marks ambiguous responses.
- If reranking is disabled, cosine similarity is stored as the explicit fallback method.
- Primary theme, candidates, scores, embedding distances, ambiguity, model IDs, and taxonomy/classification versions are persisted.

### 4. `service.py`
This module serves as the functional interface/facade between this pipeline package and HTTP API endpoints (found in `src/api/vector_routes.py` and analogous dashboard routes).
- **Triggers:** Wraps the initial vector building calls (e.g., `build_vectors_stream`).
- **Telemetry:** Exposes methods to evaluate the current status of the database and checkpoints (`vector_checkpoint_status_payload` and `pipeline_status_payload`).

---

## How it works (The Flow)

1. **Trigger:** The UI requests a vector build operation. `service.build_vectors_stream` is invoked.
2. **Analysis:** `vector_builder.py` loads the anonymized CSV, reads its schema, and identifies which columns are text responses based on headers and user-selected constraints.
3. **Model Load:** Loads the selected embedding model and, when enabled, the configured cross-encoder before replacing the collection.
4. **Resumption check:** `vector_builder.py` reads local disk checkpoints. If you have already processed e.g. 5,000 of 10,000 respondents before a crash, it skips generating embeddings for the first 5,000.
5. **Embedding, Classification & Storage:** Each batch is embedded, reduced to candidate themes, reranked, and upserted with its persisted assignment.
6. **Readiness:** The collection remains `building` until every document has compatible classification metadata. Validation then marks it `ready`.
7. **Progress Streaming:** Every batch reports embedding and classification progress until the database is ready.
