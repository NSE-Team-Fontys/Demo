# Insight Generation Pipeline (04_generation)

The `04_generation` module represents the final analytical stage of the data pipeline. It is responsible for transforming raw semantic search results retrieved from the vector database (stage `03_retrieval`) into highly structured, human-readable JSON insights. This is achieved by utilizing local Large Language Models (LLMs) via an API client interface.

## Architecture & Workflow

### 1. Semantic Theme Evidence Selection
Theme insight generation uses semantic assignment instead of hard-wiring each answer to the survey question it came from. The backend first applies any dashboard metadata filters, such as programme, cohort, location, study mode, or academic year. It then compares every remaining answer against every theme embedding from `THEME_EMBEDDING_DEFINITIONS`.

Each answer is assigned to the closest theme in embedding space. For example, if a student writes about teachers inside a general programme-organization question, that answer can still be assigned to `Teachers`. This keeps the system flexible enough for human survey behavior while still giving every answer one primary theme for frequency counting.

The retrieval helper for this is `collect_theme_documents()` in `src/pipeline/03_retrieval/service.py`. It returns the assigned documents, per-theme counts, percentages, and the total number of filtered documents.

### 2. Hierarchical Map-Reduce RAG
After semantic assignment, generation does not send only the top `LLM_CONTEXT_DOCUMENTS` answers. Instead, it reads the full assigned evidence set unless `HIERARCHICAL_RAG_MAX_DOCUMENTS` is set above `0`.

The assigned answers are split into batches controlled by `HIERARCHICAL_RAG_BATCH_DOCUMENTS`. The default is `60`, so one small summary reads up to 60 student answers. A theme with 145 assigned answers produces three map prompts: answers 1-60, 61-120, and 121-145.

Each map prompt returns the same compact JSON structure as the final insight: summary, sentiments, positive points, critical points, exact student suggestions, and subthemes. The reduce prompt then receives only these batch summaries and merges them into the final dashboard JSON. This lets the pipeline consider hundreds or thousands of unique answers without forcing all raw answers into one context window.

### 3. Prompt Engineering & Scope Enforcement
To prevent "hallucinations" and topic drift, the generation stage bounds the LLM explicitly. Using definitions from `THEME_LLM_DEFINITIONS`, the model focuses entirely on extracting information relevant to the current theme (e.g., *Support / Mentoring*). The system prompt mathematically constrains the outputs required, demanding exactly 3 positive/critical comments, up to 3 student suggestions (concrete next steps), sentiments, and discrete subthemes.

### 4. Local Model Generation
This component talks directly to local execution clients, with **llama.cpp** as the default via `http://127.0.0.1:8080`. If the UI enables model startup, selecting a model calls `POST /api/llm-models/start`. The backend starts `llama-server -hf <selected-model>` when needed or restarts its managed server when the selected model changes, applies that model's registry-owned server settings, and verifies the model identity through `/v1/models`. Generation then uses the OpenAI-compatible `/v1/chat/completions` endpoint. The selected model is resolved through `llama_cpp_models.py`, so Unsloth quant names and model-specific tuning stay centralized instead of being repeated across routes or clients.

### 5. Post-Processing & NLP Validation
Once the final JSON answer is returned, the `insight_metrics.py` component structurally evaluates the extracted "Subthemes." Instead of blindly trusting the LLM, the system performs a localized NLP intersection check (ignoring stopwords, comparing structural roots) to calculate precisely what percentage of the assigned source documents maps directly back to the LLM-generated subthemes.

### 6. Deterministic Cache Control
Since LLM generation is hardware expensive and slow, results are aggressively serialized to a file-based storage cache (`CACHE_FILE`). The pipeline has strict invalidation checks preventing stale data: if the `INSIGHT_CACHE_VERSION`, `LLM_CONTEXT_DOCUMENTS`, `HIERARCHICAL_RAG_BATCH_DOCUMENTS`, selected model settings, or the active Cross-Encoder ID changes, the cache safely treats prior generations as obsolete and forces a rebuild. Cache keys also include applied filters, so filtered summaries such as "ICT students only" do not reuse all-student insights.

---

## Core Components

### `service.py`
The orchestration engine coordinating retrieval, LLM mapping, and outputs.
- **`generate_theme_summary()`**: Pulls semantically assigned theme documents, checks filter-aware cache validity constraints (`cache_has_full_dashboard_payload`), runs the hierarchical map-reduce prompts via the selected LLM, and formats the JSON payload required by the React frontend (`positive_comments`, `student_suggestions`, `subtheme_mentions`, etc.).
- **`precompute_insights_stream()`**: A streaming generator perfect for UI progress bars. It proactively iterates over all themes in the background to build the cache asynchronously before a user navigates to a dashboard.
- **`_generate_hierarchical_json()`**: Splits assigned answers into map batches of `HIERARCHICAL_RAG_BATCH_DOCUMENTS` answers, generates one small JSON summary per batch, then reduces those summaries into one final insight.

### `llm_clients.py`
Abstract protocol (`LLMClient`) governing the interaction between Python and external local-first model runtimes.
- **`LlamaCppClient`**: Makes raw HTTP requests to llama.cpp's OpenAI-compatible API. It supports router model discovery through `/models`, single-server compatibility through `/v1/models`, managed `llama-server` startup, JSON-mode chat completions, best-effort router unloads, and termination of servers it started itself.

### `llama_cpp_models.py`
Central registry for the supported Gemma Unsloth dynamic Q4 GGUF model options and their model-specific llama.cpp tuning:
- `unsloth/gemma-4-E2B-it-qat-GGUF:UD-Q4_K_XL`
- `unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL`
- `unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M`
- `unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL`

Each registry entry owns its context size, max completion tokens, sampling controls, JSON-mode setting, and thinking flag. `llm_clients.py` only resolves the model and passes through those settings.
The E2B QAT entry also enables its bundled MTP drafter with `--spec-type draft-mtp --spec-draft-n-max 2`.

### `prompts.py`
Handles LLM IO formatting.
- **`build_prompt()`**: Injects the actual vectors into the few-shot template.
- **`build_batch_summary_prompt()`**: Builds the map-step prompt for one batch of up to `HIERARCHICAL_RAG_BATCH_DOCUMENTS` answers.
- **`build_reduce_prompt()`**: Builds the reduce-step prompt that merges batch summaries into the final dashboard JSON.
- **`parse_llm_json()`**: Uses Regex (`r"\{[\s\S]*\}"`) to safely strip Markdown boundaries (e.g., ` ```json `) emitted by some conversational instruct models, enforcing valid python dictionaries out of raw tokens strings.

### `cache.py`
Safeguards heavy computation time by tracking JSON payloads on local disk.
- Utilizes suffix swapping (`.tmp.`) during writes in `save_cache()` to prevent race conditions or corrupted JSON files on sudden process terminations.
- **`cache_matches_generation_settings()`**: Core validation ensuring `cache_version`, reranker context limits, reranker identity, and model generation settings match what the dashboard structurally requires. LLM provider/model metadata is retained for auditability, and active generation requests avoid reusing payloads produced with stale tuning.

### `insight_metrics.py`
- **`subtheme_mention_rows()`**: Iterates the documents providing term-frequency calculations. Performs basic tokenization, filters common English/Dutch stopwords, matches suffix bounds > 6 lengths, and translates counts into frontend structural pie-chart friendly percentages (`doc_percentage` and total `percentage`).

---

## Technical Configuration References
Variables strictly managing the bounds of generation performance:

| Global Constant | Location | Purpose |
|-----------------|----------|---------|
| `HIERARCHICAL_RAG_BATCH_DOCUMENTS` | `settings.py` | Number of raw answers per map-step small summary. Default: `60`. |
| `HIERARCHICAL_RAG_MAX_DOCUMENTS` | `settings.py` | Optional cap on assigned answers analyzed per theme. Default: `0`, meaning no cap. |
| `LLM_CONTEXT_DOCUMENTS` | `settings.py` | Legacy/single-prompt context limit retained for compatibility. |
| `DEFAULT_LLM_PROVIDER` | `settings.py` | Local generation runtime. Defaults to `llama.cpp`. |
| `DEFAULT_LLM_MODEL` | `settings.py` | Default llama.cpp model id. |
| `LLAMA_CPP_BASE_URL` | `settings.py` | Base URL for `llama-server`. |
| `LLAMA_CPP_SERVER_BIN` | `settings.py` | Command or absolute path used when the backend starts `llama-server`. |
| `LLAMA_CPP_STARTUP_TIMEOUT` | `settings.py` | Seconds to wait for a managed `llama-server` to become ready. |
| Model context, max tokens, temperature, top-k, thinking, JSON mode | `llama_cpp_models.py` | Per-model llama.cpp server and chat-completion tuning. |
| `INSIGHT_CACHE_VERSION` | `settings.py` | Overridden to force-invalidate existing cached structures generated by older model logic. |
| `RERANKER_MAX_CANDIDATES` | `settings.py` | Still used by ad-hoc vector query/reranking endpoints, not as the cap for hierarchical theme insights. |
