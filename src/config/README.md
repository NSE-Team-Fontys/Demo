# Configuration (`src/config`)

The `config` module is the central nervous system for constants, environment mapping, and taxonomy definitions across the entire machine learning pipeline. It prevents magic numbers, hardcoded paths, and string duplicates from polluting the logic layers (`01_anonymization` through `04_generation`).

## Core Components

### `paths.py`
Explicitly defines the file system boundaries using absolute `pathlib.Path` resolutions.
*   **Root Alignment**: Calculates `ROOT_DIR` structurally via `parents[2]` keeping everything functionally relative.
*   **State Files**: Standardizes references for checkpointing during lengthy or hardware-intensive processes (`ANON_CHECKPOINT_CSV`, `VECTOR_CHECKPOINT`).
*   **Asset References**: Holds mappings for SQLite Vector DB bindings (`survey_vector_db`), the frontend LLM cache (`gemma_cache.json`), and temporary disk upload streams (`temp_upload.csv`).

### `runtime.py`
Initializes fundamental process environments.
*   **Process Security**: Patches standard macOS Apple Silicon (M-series) multiprocessing faults by forcefully setting `"TOKENIZERS_PARALLELISM" = "false"` reducing native Python deadlocks when spawning tokenizer threads inside Flask or web workers.
*   **Graceful Operations**: Injects default PyTorch mitigations (`PYTORCH_ENABLE_MPS_FALLBACK`) avoiding application crashes when MPS handles unimplemented tensor operations.
*   **Dotenv**: Safely bootloads `.env` from physical root paths upon start.

### `settings.py`
Controls tunable runtime behavior for retrieval and local insight generation:
*   **Runtime Search Allowances**: `RERANKER_MAX_CANDIDATES` and `RERANKER_CANDIDATE_MULTIPLIER` control the candidate funnel for arbitrary vector searches.
*   **Persisted Theme Classification**: `THEME_CLASSIFICATION_CANDIDATES` controls the indexing-time theme candidate count. `THEME_AMBIGUITY_SCORE_MARGIN` controls the raw top-two score margin that marks evidence ambiguous.
*   **Hierarchical RAG Batching**: `HIERARCHICAL_RAG_BATCH_DOCUMENTS` controls the map-step group size for insight generation. The default is `60`, meaning each small summary reads up to 60 student answers before the reduce prompt merges those batch summaries. `HIERARCHICAL_RAG_MAX_DOCUMENTS=0` means no artificial cap; use a positive value only to limit analyzed answers during testing.
*   **Prompt Window Constraints**: `LLM_CONTEXT_DOCUMENTS` remains available for single-prompt fallback compatibility, while hierarchical insight generation is primarily controlled by `HIERARCHICAL_RAG_BATCH_DOCUMENTS`.
*   **Local LLM Runtime**: `DEFAULT_LLM_PROVIDER`, `DEFAULT_LLM_MODEL`, `LLAMA_CPP_BASE_URL`, `LLAMA_CPP_API_KEY`, `LLAMA_CPP_SERVER_BIN`, and `LLAMA_CPP_STARTUP_TIMEOUT` configure the llama.cpp-backed generation client. The default model is `unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL`, and the backend can start a managed `llama-server` for known registry models when the UI allows it. Per-model generation tuning such as context size, max tokens, sampling, JSON mode, and thinking is centralized in `src/pipeline/04_generation/llama_cpp_models.py`.
*   **Cache Binding**: `INSIGHT_CACHE_VERSION` forces JSON cache rotations globally. Entries are also bound to persisted classification/taxonomy settings, embedding and reranker identities, ambiguity rules, the selected LLM, hierarchical batch size, and dashboard filters.

### `themes.py`
Encapsulates structural constraints and standard categorizations.
*   **Theme Scope Context**: Maps the UI taxonomy (`THEMES_LIST`) to LLM scope definitions and multilingual embedding prototypes. `THEME_CLASSIFICATION_VERSION` and `THEME_TAXONOMY_VERSION` invalidate incompatible vector data. Low-information responses are routed deterministically.
*   **Data Inference**: Exposes analytical structures like `METADATA_COLS` ensuring dynamic parsers (`src/utils/file_parsers.py`) can accurately distinguish metadata parameters from raw text surveys.
*   **Alias Mappings**: Resolves the "Dutch vs English" metadata headache via `METADATA_ALIASES` and `SOURCE_METADATA_ALIASES`, unifying differing raw survey column structures (e.g. `academic_year` mapped simultaneously with `Jaar`).

### `response_quality.py`
Contains the complete low-information response classifier and its editable policy. Add words or complete phrases to `LOW_INFORMATION_RESPONSES`; matching is case-insensitive and ignores accents and punctuation. Punctuation-only answers such as `.`, `...`, `/`, and `-` are already classified as low-information without adding each symbol.
