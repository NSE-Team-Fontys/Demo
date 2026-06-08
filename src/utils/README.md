# Utilities (`src/utils`)

The `utils` module provides shared, low-level technical infrastructure and helper functions consumed across the analytical pipeline. It is built to ensure consistent file IO, heuristic parsing, and optimal hardware acceleration routing for PyTorch-backed anonymization, embedding, and reranking models.

## Core Components

### `file_parsers.py`

This script manages robust, fault-tolerant dataset ingestion. Because survey data can arrive in numerous formats with varying delimiters and encodings, this utility ensures that upstream systems only ever receive clean `pandas.DataFrame` objects.

*   **Intelligent Separator Sniffing (`detect_sep`)**: 
    European tabular data notoriously suffers from mixing `,` and `;` delimiters. This algorithm:
    1. Reads a 50-line sample ignoring encoding errors.
    2. Attempts standard `csv.Sniffer` resolution.
    3. Triggers a fallback heuristic scoring system. It evaluates each candidate delimiter against the sample, tracking column count mode, punishing variance in row sizing, and penalizing parsing errors. It reliably deduces the correct split string without user intervention.
*   **Column Type Inference (`is_questionnaire_column`)**:
    Differentiates metadata columns (e.g., `institution`, `study_mode`) from actual survey text responses. It performs regex-like checks (checking for `?` characters, specific Dutch prefix queries) and explicitly excludes hardcoded demographics imported from `METADATA_COLS`.
*   **File State Management**: 
    Controls the physical disk state of uploaded datasets via `save_uploaded_file` and `get_upload_path`, maintaining metadata in an intermediary `upload_info.json` to persist state across server reboots.

### `model_device.py`

This is the central hardware acceleration router for PyTorch and `sentence_transformers`. It ensures that embedding computations (`02_embedding`) and cross-encoder reranking (`03_retrieval`) operate on the fastest silicon available on the host machine. Stage `04_generation` now uses an external llama.cpp server, so it is configured through `src.config.settings` rather than this PyTorch device router.

*   **Auto-Detection Hardware Cascading**:
    `get_model_device()` implements a cascade fallback:
    1.  **NVIDIA CUDA or AMD ROCm GPUs**: Checks `torch.cuda.is_available()`. PyTorch intentionally exposes ROCm/HIP devices through the same `cuda` API and device string.
    2.  **Apple Silicon (MPS)**: Injects safe checks to evaluate if the `mps` backend is built and ready, allowing M1/M2/M3 chips to accelerate heavy transformer workloads natively.
    3.  **CPU Fallback**: Defaults to `cpu` if no dedicated accelerator is found.
*   **Environment Variable Overrides**:
    The auto-detection can be manually clamped by setting the `MODEL_DEVICE` environment variable (e.g., `MODEL_DEVICE=cpu`, `MODEL_DEVICE=cuda:0`, or `MODEL_DEVICE=rocm`). The `rocm` and `hip` aliases are normalized to PyTorch's required `cuda` device string.
*   **Pipeline Normalization (`get_pipeline_device`)**:
    HuggingFace standard pipelines strictly demand integer configurations (e.g., `0` for CUDA device 0) or specific PyTorch classes (`torch.device('mps')`) rather than generic string descriptors. This transformer function patches those inconsistencies automatically. 

---

## Technical Configuration References

| Environment Variable | Supported Values | Fallback | Purpose |
| :--- | :--- | :--- | :--- |
| `MODEL_DEVICE` | `auto`, `cuda`, `rocm`, `hip`, `mps`, `cpu` | `auto` | Forces the machine learning pipeline into a specific processing architecture. |
