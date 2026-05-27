# Insight Generation Pipeline (04_generation)

The `04_generation` module represents the final analytical stage of the data pipeline. It is responsible for transforming raw semantic search results retrieved from the vector database (stage `03_retrieval`) into highly structured, human-readable JSON insights. This is achieved by utilizing local Large Language Models (LLMs) via an API client interface.

## Architecture & Workflow

### 1. Document Context Selection
After retrieving a pool of relevant documents from the Cross-Encoder reranker (`03_retrieval`), the pipeline trims the result set to fit within the prompt context window of the LLM. Controlled by the `LLM_CONTEXT_DOCUMENTS` config, the topmost highly relevant excerpts are selected as the exact ground-truth evidence provided to the model.

### 2. Prompt Engineering & Scope Enforcement
To prevent "hallucinations" and topic drift, the generation stage bounds the LLM explicitly. Using definitions from `THEME_DEFINITIONS`, the model focuses entirely on extracting information relevant to the current theme (e.g., *Support / Mentoring*). The system prompt mathematically constrains the outputs required, demanding exactly 3 positive/critical comments, up to 3 student suggestions (concrete next steps), sentiments, and discrete subthemes.

### 3. Local Model Generation 
This component talks directly to local execution clients (primarily **Ollama** via `http://localhost:11434`). It pulls missing models on-demand if allowed, and configures the generation to enforce JSON mode (`"format": "json"`). It manages execution timeouts (up to 10 minutes default) preventing runaway generations.

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
- **`OllamaClient`**: Makes raw HTTP POST/GET requests to Ollama's REST API. Manages `/api/tags` checking, model `/api/pull` mechanics, and JSON-bounded `/api/generate` calls. Includes a memory purge function (`keep_alive: 0`) for hardware rotation.
- **`LlamaCppClient`**: A structural stub for future native `llama.cpp` integration.

### `prompts.py`
Handles LLM IO formatting.
- **`build_prompt()`**: Injects the actual vectors into the few-shot template.
- **`parse_llm_json()`**: Uses Regex (`r"\{[\s\S]*\}"`) to safely strip Markdown boundaries (e.g., ` ```json `) emitted by some conversational instruct models, enforcing valid python dictionaries out of raw tokens strings.

### `cache.py`
Safeguards heavy computation time by tracking JSON payloads on local disk.
- Utilizes suffix swapping (`.tmp.`) during writes in `save_cache()` to prevent race conditions or corrupted JSON files on sudden process terminations.
- **`cache_matches_generation_settings()`**: Core validation ensuring `cache_version`, reranker context limits, and retrieval hardware match what the dashboard structurally requires.

### `insight_metrics.py`
- **`subtheme_mention_rows()`**: Iterates the documents providing term-frequency calculations. Performs basic tokenization, filters common English/Dutch stopwords, matches suffix bounds > 6 lengths, and translates counts into frontend structural pie-chart friendly percentages (`doc_percentage` and total `percentage`).

---

## Technical Configuration References
Variables strictly managing the bounds of generation performance:

| Global Constant | Location | Purpose |
|-----------------|----------|---------|
| `LLM_CONTEXT_DOCUMENTS` | `settings.py` | Maximum subset of documents to feed into a single LLM prompt context window. |
| `INSIGHT_CACHE_VERSION` | `settings.py` | Overridden to force-invalidate existing cached structures generated by older model logic. |
| `RERANKER_MAX_CANDIDATES` | `settings.py` | Governs the maximum top-k slice passed out from retrieval into generation frequency math. |