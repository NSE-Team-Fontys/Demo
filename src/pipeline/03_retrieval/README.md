# Retrieval Pipeline (03_retrieval)

The `03_retrieval` module has two deliberately separate paths. Predefined dashboard themes read persisted assignments from Chroma metadata without loading ML models. Arbitrary queries and generated subthemes use dense retrieval followed by optional cross-encoder reranking.

## Architecture & Workflow

### 1. Vector Search (Dense Retrieval)
When a query is received, it is mathematically transformed into an embedding vector using the same embedding model that was used during the ingestion phase (e.g., `src.pipeline.02_embedding`). 
The core search occurs within ChromaDB, which computes similarity scores (cosine distance) between the query vector and all document vectors. 

### 2. Metadata Filtering
Before computing distance, the retrieval algorithm applies heavy metadata filtering capabilities via Chroma DB's `where` conditions. The filters operate over canonical keys, accommodating aliases dynamically:
- `institutions`, `academic_years`, `locations`, `programmes`, `study_modes`, `cohorts`.
This ensures that users can drill down and isolate only the demographic or institutional slices they are interested in.

### 3. Cross-Encoder Reranking
Because standard dense embeddings (especially Bi-Encoders) might miss subtle semantic nuances, the pipeline includes an optional second stage. The top $N$ documents retrieved by ChromaDB are passed into a **Cross-Encoder Model** (default: `zeroentropy/zerank-2-reranker`).
- Unlike standard embedding models, a cross-encoder processes the `(Question, Document)` pair simultaneously.
- It outputs an independent relevance score.
- The retrieved results are then sorted based on this high-fidelity score (`reranker_score`), vastly improving the relevance of what is passed onto the `04_generation` step.

### 4. Persisted Dashboard Theme Evidence
`collect_theme_documents()` queries scalar classification metadata written during vector construction:
- Frequency counts use only `theme_primary`, so every response is counted once.
- Definite evidence is a non-ambiguous primary assignment.
- Ambiguous evidence may be returned for each persisted candidate theme.
- Existing dashboard metadata filters are combined with primary/candidate filters in Chroma.
- Missing, building, or configuration-incompatible classification data fails with a fresh-build requirement instead of loading models at read time.

---

## Core Components

### `service.py`
The brain of the retrieval pipeline. This script exports the main APIs consumed by the routing layers.
- **Connection & Model Management**: Efficiently loads embedding and cross-encoder models with LRU caching to prevent Memory Overflows. 
- **Filters Engine (`build_where_filter`)**: Maps complex front-end filter payloads into valid Chroma `$and` / `$or` queries.
- **`rerank_documents()`**: Fuses the dense results with the cross-encoder predictions to sort documents. It gracefully degrades if the reranker is disabled, defaulting to cosine similarity (`1 - distance`).
- **`collect_theme_documents()`**: Returns definite and ambiguous persisted evidence for predefined themes without embedding or reranking.
- **`theme_distribution()`**: Counts persisted primary assignments only.
- **Options Discovery (`filter_options_payload`)**: Reads the database metadata to dynamically generate dropdown filter categories available on the frontend dashboard. 

### `reranker_models.py`
Dedicated strictly to the management of cross-encoder models utilizing the `sentence_transformers` library.
*   **Hardware Acceleration**: Hooks into `src.utils.model_device` to utilize GPU/MPS hardware automatically.
*   **Caching (`@lru_cache`)**: Keeps models residing in memory aggressively to ensure retrieval lag stays well below acceptable limits on subsequent requests.
*   **Offline Mode (`_downloads_disabled`)**: Native support for air-gapped or restricted network environments (respecting Hugging Face configuration rules).

### `query_cli.py`
An interactive command-line interface for internal testing and debugging of the retrieval logic.
- Execute it directly to spawn an interactive shell connected to the vector store (`Survey Vector DB — Query Interface`).
- Run runtime commands (e.g., `/inst <value>` to isolate institutions, `/n <num>` to expand vector limits).
- Provides instant transparency into generated similarity numbers and runtime models.

---

## Configuration & Environment Variables

The retrieval environment can be heavily controlled via system variables (mostly handled in `reranker_models.py`):

| Variable | Description | Default |
|----------|-------------|---------|
| `RERANKER_ENABLED` | Toggles the secondary reranking stage (`true` / `false`) | `true` |
| `RERANKER_MODEL` | Hugging Face ID of the Cross-Encoder model. | `zeroentropy/zerank-2-reranker` |
| `HF_HUB_OFFLINE` | Set to 1 to freeze downloads from HF hub and utilize local cache only. | `0` |
| `RERANKER_TRUST_REMOTE_CODE` | Enables custom execution for complex models dynamically. | `false` |
