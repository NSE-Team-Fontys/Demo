# Anonymization Pipeline

This folder contains the core logic for the data anonymization feature. The pipeline is designed to process textual data in large datasets (e.g., CSV/Excel files) incrementally, identify Personally Identifiable Information (PII) using multiple NLP and rule-based layers, and substitute them with generic tags (like `[NAME]`, `[DATE]`, `[LOCATION]`).

## Architecture & Structure

The folder is structured to separate concerns between HTTP service boundaries, processing engine logic, checkpointing/reporting, and actual NLP inference (layers).

- **`service.py`**: The main entry point used by the API routes. Handles file parsing/inspection, starts the anonymization job through the engine, and returns statuses or processed payloads.
- **`engine.py`**: The orchestration core. It loops through the requested columns in a dataset, applies the anonymizers chunk-by-chunk using batching, and handles the logic for storing intermediate progress boundaries to disk for resumption.
- **`checkpoints.py`**: Manages the persistence of intermediate state (a "checkpoint") during a long-running anonymization task. This allows the system to seamlessly resume if a process is interrupted.
- **`reporting.py`**: Generates a summary log/report after an anonymization run, tracking metrics such as the total volume of text processed, rows affected, and completion status.
- **`layers/` (The Privacy Pipeline)**:
  - This directory handles the actual detection and masking of PII elements within a given text string or batch of strings.
  - **`layer1_presidio.py`**: Uses the Microsoft Presidio analyzer for rule-based and standard NER entity matching.
  - **`layer2_eu_pii.py` & `layer2_openai_privacy_filter.py`**: These serve as more advanced, heavy-weight Machine Learning layers ensuring higher precision over specific domain contexts (e.g., European PII norms). 
  - **`privacy_pipeline.py` & `layer_utils.py`**: Orchestrate the interplay between the multiple running layers.

## How it Works (Late-Masking Approach)

A core innovation in how this anonymization engine operates is the **Late-Masking Methodology**:

1. **Span Collection**: Rather than each layer finding PII and immediately replacing it in the text sequentially (which often leads to data corruption, double-masking issues, or string-offset invalidation), all active layers independently return a list of "spans" indicating the starts, ends, and entity tags (e.g., `(10, 15, "[NAME]")`).
2. **Merging & Normalization**: `privacy_pipeline.py` merges spans collected from Layer 1 and Layer 2 models securely. It filters out false positives or honorifics and extends text boundaries (e.g., checking possessive forms or quotes) to cleanly cover the intended string target.
3. **Single-Pass Text Substitution**: Once the engine resolves the final set of normalized and overlapping spans, it replaces all matching segments backward through the string in a single mutation. 

## Carry-forward Detection

The pipeline maintains memory of certain extracted entities across the document chunk (Carry-forward logic) by observing high-confidence tags (like a plausible name match). If `"Mr. Johnson"` is found explicitly, the pipeline will trace `"Johnson"` on subsequent partial occurrences, masking it consistently where a context-blind model might struggle.

## Execution Flow

1. An HTTP request comes in dictating columns and requested layers. `service.anonymize_uploaded_file` receives it.
2. `engine.process_file_with_layers` loads the dataframe and evaluates if there is an existing checkpoint. 
3. Iterating per targeted column, applying chunked batching.
4. Each chunk delegates to `privacy_pipeline.py` where:
   - Layer 1 models examine the batch.
   - Layer 2 models (usually placed on MPS/CUDA devices) are fed the batch.
   - Spans are aggregated, and texts are updated.
5. Every *N* batches, a checkpoint is committed to disk safely.
6. Upon finishing all columns, `reporting.py` compiles the run details, and `checkpoints.py` clears out temporary states.
