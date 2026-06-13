# Graph Report - .  (2026-06-12)

## Corpus Check
- Corpus is ~21,090 words - fits in a single context window. You may not need a graph.

## Summary
- 345 nodes · 632 edges · 27 communities (19 shown, 8 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Blocklist Anonymization Engine|Blocklist Anonymization Engine]]
- [[_COMMUNITY_EU PII Detection|EU PII Detection]]
- [[_COMMUNITY_llama.cpp Model Config|llama.cpp Model Config]]
- [[_COMMUNITY_Embedding Model Runtime|Embedding Model Runtime]]
- [[_COMMUNITY_Embedding Retrieval Concepts|Embedding Retrieval Concepts]]
- [[_COMMUNITY_Reranker Model Runtime|Reranker Model Runtime]]
- [[_COMMUNITY_Insight Cache and LLM|Insight Cache and LLM]]
- [[_COMMUNITY_Anonymization API Routes|Anonymization API Routes]]
- [[_COMMUNITY_Presidio Detection Layer|Presidio Detection Layer]]
- [[_COMMUNITY_Anonymization Service|Anonymization Service]]
- [[_COMMUNITY_Anonymization Design|Anonymization Design]]
- [[_COMMUNITY_Insight Prompt Generation|Insight Prompt Generation]]
- [[_COMMUNITY_Checkpoint Persistence|Checkpoint Persistence]]
- [[_COMMUNITY_Vector Search CLI|Vector Search CLI]]
- [[_COMMUNITY_Embedding Package|Embedding Package]]
- [[_COMMUNITY_Retrieval Package|Retrieval Package]]
- [[_COMMUNITY_Generation Package|Generation Package]]
- [[_COMMUNITY_Configuration Package|Configuration Package]]
- [[_COMMUNITY_Anonymization Layers|Anonymization Layers]]
- [[_COMMUNITY_Pipeline Packages|Pipeline Packages]]
- [[_COMMUNITY_Utility Package|Utility Package]]

## God Nodes (most connected - your core abstractions)
1. `LlamaCppClient` - 21 edges
2. `process_file_with_layers()` - 15 edges
3. `collect_presidio_spans()` - 13 edges
4. `eu_pii_collect_batch()` - 13 edges
5. `get_model_device()` - 13 edges
6. `ensure_eu_pii_available()` - 11 edges
7. `process_chunk_sync()` - 11 edges
8. `load_embedding_model()` - 11 edges
9. `normalize_for_ner()` - 10 edges
10. `build_vector_db_stream()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `_read_input()` --calls--> `Path`  [INFERRED]
  pipeline/01_anonymization/engine.py → utils/file_parsers.py
- `_read_input()` --calls--> `detect_sep()`  [INFERRED]
  pipeline/01_anonymization/engine.py → utils/file_parsers.py
- `_read_input()` --calls--> `read_dataframe()`  [INFERRED]
  pipeline/01_anonymization/engine.py → utils/file_parsers.py
- `process_file_with_layers()` --calls--> `Path`  [INFERRED]
  pipeline/01_anonymization/engine.py → utils/file_parsers.py
- `process_file_with_layers()` --calls--> `detect_sep()`  [INFERRED]
  pipeline/01_anonymization/engine.py → utils/file_parsers.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Survey Analytics Pipeline Flow** — 01_anonymization_readme_anonymization_pipeline, 02_embedding_readme_embedding_pipeline, 03_retrieval_readme_retrieval_pipeline, 04_generation_readme_insight_generation_pipeline [INFERRED 0.95]
- **Resumable Long-Running Processing** — config_readme_path_management, 01_anonymization_readme_checkpoint_resumption, 02_embedding_readme_checkpoint_resumption [INFERRED 0.85]
- **Shared Accelerated Model Execution** — 02_embedding_readme_sentence_transformer, 03_retrieval_readme_cross_encoder_reranking, utils_readme_hardware_acceleration_routing [EXTRACTED 1.00]

## Communities (27 total, 8 thin omitted)

### Community 0 - "Blocklist Anonymization Engine"
Cohesion: 0.10
Nodes (33): apply_blocklist(), load_blocklist(), Return the current custom word blocklist, or [] if none saved., Persist the blocklist to disk, deduplicating and stripping whitespace., Replace every whole-word (case-insensitive) occurrence of each blocklist     ent, save_blocklist(), process_file_with_layers(), Run only the verification step on already-existing original + anonymized files. (+25 more)

### Community 1 - "EU PII Detection"
Cohesion: 0.10
Nodes (33): _apply_entities(), _config_allows_tag(), ensure_eu_pii_available(), eu_pii_collect_batch(), eu_pii_safeguard_anonymize(), eu_pii_safeguard_anonymize_batch(), _eu_pii_tag(), _is_numeric_or_id() (+25 more)

### Community 2 - "llama.cpp Model Config"
Cohesion: 0.12
Nodes (8): llama_cpp_model_options(), LlamaCppGenerationSettings, LlamaCppModel, resolve_llama_cpp_model(), LlamaCppClient, LocalModelConnectionError, Any, RuntimeError

### Community 3 - "Embedding Model Runtime"
Cohesion: 0.11
Nodes (28): describe_embedding_runtime(), _downloads_disabled(), load_embedding_model(), _load_embedding_model_cached(), Load a SentenceTransformer embedding model on the preferred local device.      W, Release cached embedding models and return unused accelerator memory., _trust_remote_code_enabled(), unload_embedding_models() (+20 more)

### Community 4 - "Embedding Retrieval Concepts"
Cohesion: 0.08
Nodes (32): ChromaDB Vector Indexing, Embedding Pipeline, Vector Metadata Enrichment, SentenceTransformer Embedding Model, Streaming Batch Processing, Cosine Similarity Fallback, Cross-Encoder Reranking, Dense Retrieval (+24 more)

### Community 5 - "Reranker Model Runtime"
Cohesion: 0.14
Nodes (29): describe_reranker_runtime(), _downloads_disabled(), load_reranker_model(), _load_reranker_model_cached(), reranker_enabled(), selected_reranker_model(), _trust_remote_code_enabled(), build_where_filter() (+21 more)

### Community 6 - "Insight Cache and LLM"
Cohesion: 0.16
Nodes (21): cache_has_full_dashboard_payload(), cache_matches_generation_settings(), load_cache(), save_cache(), get_llm_client(), LLMClient, _cache_filters_match(), _cache_key() (+13 more)

### Community 7 - "Anonymization API Routes"
Cohesion: 0.08
Nodes (5): _filters_from_payload(), precompute_insights(), theme_summary(), _filters_from_args(), query_vectors()

### Community 8 - "Presidio Detection Layer"
Cohesion: 0.17
Nodes (17): AnalyzerEngine, anonymize_with_presidio(), _build_analyzer(), build_presidio_operators(), ensure_presidio_available(), _ensure_spacy_models(), _get_analyzer(), presidio_masking_spec() (+9 more)

### Community 9 - "Anonymization Service"
Cohesion: 0.29
Nodes (11): anonymize_uploaded_file(), inspect_anonymized_file(), inspect_uploaded_file(), run_anonymize_check_stream(), Path, detect_sep(), get_upload_path(), preview_records() (+3 more)

### Community 10 - "Anonymization Design"
Cohesion: 0.22
Nodes (9): Anonymization Pipeline, Carry-Forward Detection, Anonymization Checkpoint Resumption, Late-Masking Methodology, Layered PII Detection, Single-Pass Text Substitution, PII Span Collection, Span Merging and Normalization (+1 more)

### Community 11 - "Insight Prompt Generation"
Cohesion: 0.40
Nodes (3): build_prompt(), default_prompt(), parse_llm_json()

### Community 13 - "Vector Search CLI"
Cohesion: 0.67
Nodes (3): main(), Search the vector database.      Args:         query:       Natural language que, search()

## Knowledge Gaps
- **9 isolated node(s):** `DataFrame`, `Path Management`, `Runtime Environment Initialization`, `Single-Pass Text Substitution`, `Carry-Forward Detection` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `process_file_with_layers()` connect `Blocklist Anonymization Engine` to `EU PII Detection`, `Embedding Model Runtime`, `Anonymization Service`?**
  _High betweenness centrality (0.176) - this node is a cross-community bridge._
- **Why does `get_model_device()` connect `Embedding Model Runtime` to `Blocklist Anonymization Engine`, `Reranker Model Runtime`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `LlamaCppClient` connect `llama.cpp Model Config` to `Insight Cache and LLM`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `process_file_with_layers()` (e.g. with `Path` and `detect_sep()`) actually correct?**
  _`process_file_with_layers()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `get_model_device()` (e.g. with `process_file_with_layers()` and `describe_embedding_runtime()`) actually correct?**
  _`get_model_device()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Static application configuration.`, `Stage 01: PII anonymization and privacy filters.`, `Return the current custom word blocklist, or [] if none saved.` to the rest of the system?**
  _56 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Blocklist Anonymization Engine` be split into smaller, more focused modules?**
  _Cohesion score 0.09581646423751687 - nodes in this community are weakly interconnected._