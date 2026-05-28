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
Controls the tunable heuristic behaviors for generative execution matching:
*   **Vector Allowances**: `RERANKER_MAX_CANDIDATES` and `RERANKER_CANDIDATE_MULTIPLIER` control the "funnel width" of vector embeddings parsed by the costly cross-encoder pipeline.
*   **Prompt Window Constraints**: `LLM_CONTEXT_DOCUMENTS` binds maximum prompt inject lengths.
*   **Cache Binding**: `INSIGHT_CACHE_VERSION` strictly forces JSON cache rotations globally.

### `themes.py`
Encapsulates structural constraints and standard categorizations.
*   **Theme Scope Context**: Maps the UI taxonomy (`THEMES_LIST`) to robust instructional prompts (`THEME_DEFINITIONS`) heavily utilized in step `04_generation` to steer instructions and prevent hallucinations.
*   **Data Inference**: Exposes analytical structures like `METADATA_COLS` ensuring dynamic parsers (`src/utils/file_parsers.py`) can accurately distinguish metadata parameters from raw text surveys.
*   **Alias Mappings**: Resolves the "Dutch vs English" metadata headache via `METADATA_ALIASES` and `SOURCE_METADATA_ALIASES`, unifying differing raw survey column structures (e.g. `academic_year` mapped simultaneously with `Jaar`).