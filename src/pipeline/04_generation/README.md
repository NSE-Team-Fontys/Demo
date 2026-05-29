# Insight Generation Pipeline (04_generation)

The `04_generation` module represents the final analytical stage of the data pipeline. It is responsible for transforming raw semantic search results retrieved from the vector database (stage `03_retrieval`) into highly structured, human-readable JSON insights. This is achieved by utilizing local Large Language Models (LLMs) via an API client interface.

## Architecture & Workflow

### 1. Document Context Selection
After retrieving a pool of relevant documents from the Cross-Encoder reranker (`03_retrieval`), the pipeline trims the result set to fit within the prompt context window of the LLM. Controlled by the `LLM_CONTEXT_DOCUMENTS` config, the topmost highly relevant excerpts are selected as the exact ground-truth evidence provided to the model.

### 2. Prompt Engineering & Scope Enforcement
To prevent "hallucinations" and topic drift, the generation stage bounds the LLM explicitly. Using definitions from `THEME_DEFINITIONS`, the model focuses entirely on extracting information relevant to the current theme (e.g., *Support / Mentoring*). The system prompt mathematically constrains the outputs required, demanding exactly 3 positive/critical comments, up to 3 student suggestions (concrete next steps), sentiments, and discrete subthemes.

### 3. Local Model Generation 
This component talks directly to local execution clients, with **llama.cpp** as the default via `http://127.0.0.1:8080`. If the UI enables model startup and no llama.cpp server is reachable, the backend starts `llama-server -hf <selected-model>` for the selected registry model, applies that model's registry-owned server settings, waits for `/v1/models`, then calls the OpenAI-compatible `/v1/chat/completions` endpoint with the selected model's generation settings. The selected model is resolved through `llama_cpp_models.py`, so Unsloth quant names and model-specific tuning stay centralized instead of being repeated across routes or clients.

### 4. Post-Processing & NLP Validation
Once JSON answers are returned, the `insight_metrics.py` component structurally evaluates the extracted "Subthemes." Instead of blindly trusting the LLM, the system performs a localized NLP intersection check (ignoring stopwords, comparing structural roots) to calculate precisely what percentage of the actual document vector batch maps directly back to the LLM-generated subthemes.

### 5. Deterministic Cache Control
Since LLM generation is hardware expensive and slow, results are aggressively serialized to a file-based storage cache (`CACHE_FILE`). The pipeline has "strict invalidation" checks preventing stale data: if the `INSIGHT_CACHE_VERSION`, `LLM_CONTEXT_DOCUMENTS`, or the active Cross-Encoder ID changes, the cache safely treats prior generations as obsolete and forces a system rebuild to maintain Dashboard payload integrity.

---

## Core Components

### `service.py`
The orchestration engine coordinating retrieval, LLM mapping, and outputs.
- **`generate_theme_summary()`**: Pulls documents, checks cache validity constraints (`cache_has_full_dashboard_payload`), runs the prompt via the selected LLM, and formats the extensive JSON payload required by the React frontend (`positive_comments`, `student_suggestions`, `subtheme_mentions`, etc.).
- **`precompute_insights_stream()`**: A streaming generator perfect for UI progress bars. It proactively iterates over all themes in the background to build the cache asynchronously before a user navigates to a dashboard.

### `llm_clients.py`
Abstract protocol (`LLMClient`) governing the interaction between Python and external local-first model runtimes.
- **`LlamaCppClient`**: Makes raw HTTP requests to llama.cpp's OpenAI-compatible API. It supports router model discovery through `/models`, single-server compatibility through `/v1/models`, managed `llama-server` startup, JSON-mode chat completions, best-effort router unloads, and termination of servers it started itself.

### `llama_cpp_models.py`
Central registry for the supported Gemma Unsloth dynamic Q4 GGUF model options and their model-specific llama.cpp tuning:
- `unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL`
- `unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL`
- `unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M`
- `unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL`

Each registry entry owns its context size, max completion tokens, sampling controls, JSON-mode setting, and thinking flag. `llm_clients.py` only resolves the model and passes through those settings.

### `prompts.py`
Handles LLM IO formatting.
- **`build_prompt()`**: Injects the actual vectors into the few-shot template.
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
| `LLM_CONTEXT_DOCUMENTS` | `settings.py` | Maximum subset of documents to feed into a single LLM prompt context window. |
| `DEFAULT_LLM_PROVIDER` | `settings.py` | Local generation runtime. Defaults to `llama.cpp`. |
| `DEFAULT_LLM_MODEL` | `settings.py` | Default llama.cpp model id. |
| `LLAMA_CPP_BASE_URL` | `settings.py` | Base URL for `llama-server`. |
| `LLAMA_CPP_SERVER_BIN` | `settings.py` | Command or absolute path used when the backend starts `llama-server`. |
| `LLAMA_CPP_STARTUP_TIMEOUT` | `settings.py` | Seconds to wait for a managed `llama-server` to become ready. |
| Model context, max tokens, temperature, top-k, thinking, JSON mode | `llama_cpp_models.py` | Per-model llama.cpp server and chat-completion tuning. |
| `INSIGHT_CACHE_VERSION` | `settings.py` | Overridden to force-invalidate existing cached structures generated by older model logic. |
| `RERANKER_MAX_CANDIDATES` | `settings.py` | Governs the maximum top-k slice passed out from retrieval into generation frequency math. |
