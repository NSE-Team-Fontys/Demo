# Graph Report - .  (2026-06-13)

## Corpus Check
- Corpus is ~32,424 words - fits in a single context window. You may not need a graph.

## Summary
- 447 nodes · 851 edges · 32 communities (24 shown, 8 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 43 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Anonymization Filters|Anonymization Filters]]
- [[_COMMUNITY_Insight Pipeline Flow|Insight Pipeline Flow]]
- [[_COMMUNITY_Theme Classification|Theme Classification]]
- [[_COMMUNITY_Llama Model Configuration|Llama Model Configuration]]
- [[_COMMUNITY_Embedding Runtime|Embedding Runtime]]
- [[_COMMUNITY_Anonymization API|Anonymization API]]
- [[_COMMUNITY_Anonymization Service|Anonymization Service]]
- [[_COMMUNITY_Insight Cache and LLM|Insight Cache and LLM]]
- [[_COMMUNITY_Anonymization Quality|Anonymization Quality]]
- [[_COMMUNITY_Retrieval and Reranking|Retrieval and Reranking]]
- [[_COMMUNITY_OpenAI Privacy Filter|OpenAI Privacy Filter]]
- [[_COMMUNITY_PII False Positive Checks|PII False Positive Checks]]
- [[_COMMUNITY_Generation Prompts|Generation Prompts]]
- [[_COMMUNITY_Processing Checkpoints|Processing Checkpoints]]
- [[_COMMUNITY_Vector Query CLI|Vector Query CLI]]
- [[_COMMUNITY_Frontend Package Metadata|Frontend Package Metadata]]
- [[_COMMUNITY_Embedding Stage Package|Embedding Stage Package]]
- [[_COMMUNITY_Retrieval Stage Package|Retrieval Stage Package]]
- [[_COMMUNITY_Generation Stage Package|Generation Stage Package]]
- [[_COMMUNITY_Static Configuration Package|Static Configuration Package]]
- [[_COMMUNITY_Anonymization Layers Package|Anonymization Layers Package]]
- [[_COMMUNITY_Pipeline Stage Package|Pipeline Stage Package]]
- [[_COMMUNITY_Utility Package|Utility Package]]

## God Nodes (most connected - your core abstractions)
1. `LlamaCppClient` - 21 edges
2. `get_model_device()` - 20 edges
3. `build_vector_db_stream()` - 18 edges
4. `detect_sep()` - 18 edges
5. `build_vector_db()` - 16 edges
6. `describe_model_device()` - 15 edges
7. `process_file_with_layers()` - 14 edges
8. `collect_presidio_spans()` - 14 edges
9. `eu_pii_collect_batch()` - 13 edges
10. `read_dataframe()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `Structural Shape Rules` --semantically_similar_to--> `Shared Span Plausibility Filters`  [INFERRED] [semantically similar]
  MASKING_TUNING.txt → ANONYMIZATION_IMPROVEMENTS.md
- `Privacy Threshold Tradeoff` --semantically_similar_to--> `Confidence Score Thresholds`  [INFERRED] [semantically similar]
  MASKING_TUNING.txt → ANONYMIZATION_IMPROVEMENTS.md
- `Late-Masking Methodology` --semantically_similar_to--> `Late-Masking Filter Chain`  [INFERRED] [semantically similar]
  src/pipeline/01_anonymization/README.md → ANONYMIZATION_IMPROVEMENTS.md
- `ChromaDB Dependency` --semantically_similar_to--> `ChromaDB`  [INFERRED] [semantically similar]
  requirements-common.txt → README.md
- `Persisted Theme Classification` --semantically_similar_to--> `Persisted Theme Assignments`  [INFERRED] [semantically similar]
  src/pipeline/02_embedding/README.md → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **End-to-End Survey Insight Pipeline** — readme_stage_01_anonymization, readme_stage_02_embedding, readme_stage_03_retrieval, readme_stage_04_generation [EXTRACTED 1.00]
- **Anonymization Quality Control Stack** — anonymization_improvements_confidence_score_thresholds, anonymization_improvements_shared_plausibility_filters, anonymization_improvements_custom_word_blocklist, 01_anonymization_readme_late_masking_methodology [EXTRACTED 1.00]
- **Persisted Theme Evidence Lifecycle** — 02_embedding_readme_persisted_theme_classification, 03_retrieval_readme_persisted_dashboard_theme_evidence, 04_generation_readme_semantic_theme_evidence_selection [EXTRACTED 1.00]

## Communities (32 total, 8 thin omitted)

### Community 0 - "Anonymization Filters"
Cohesion: 0.05
Nodes (67): apply_blocklist(), load_blocklist(), Return the current custom word blocklist, or [] if none saved., Persist the blocklist to disk, deduplicating and stripping whitespace., Replace every whole-word (case-insensitive) occurrence of each blocklist     ent, save_blocklist(), process_file_with_layers(), Run only the verification step on already-existing original + anonymized files. (+59 more)

### Community 1 - "Insight Pipeline Flow"
Cohesion: 0.06
Nodes (44): Embedding Pipeline, Low-Information Response Routing, Persisted Theme Classification, Resumable Chroma Upserts, Vector Builder, Cross-Encoder Reranking, Dense Vector Retrieval, Metadata Filtering (+36 more)

### Community 2 - "Theme Classification"
Cohesion: 0.13
Nodes (29): Release cached embedding models and return unused accelerator memory., unload_embedding_models(), classification_config(), classify_theme_batch(), encode_theme_definitions(), _low_information_metadata(), Classify one embedding batch and run at most one reranker prediction call., theme_definition_text() (+21 more)

### Community 3 - "Llama Model Configuration"
Cohesion: 0.12
Nodes (8): llama_cpp_model_options(), LlamaCppGenerationSettings, LlamaCppModel, resolve_llama_cpp_model(), LlamaCppClient, LocalModelConnectionError, Any, RuntimeError

### Community 4 - "Embedding Runtime"
Cohesion: 0.11
Nodes (28): describe_embedding_runtime(), _downloads_disabled(), load_embedding_model(), _load_embedding_model_cached(), Load a SentenceTransformer embedding model on the preferred local device.      W, _trust_remote_code_enabled(), describe_reranker_runtime(), _downloads_disabled() (+20 more)

### Community 5 - "Anonymization API"
Cohesion: 0.07
Nodes (11): register_blueprints(), _build_filter_grid(), _filters_from_payload(), precompute_insights(), precompute_preview(), Return cross-product size for the given filter dimensions., Expand the cross-product of the requested filter dimensions., theme_summary() (+3 more)

### Community 6 - "Anonymization Service"
Cohesion: 0.18
Nodes (23): anonymize_uploaded_file(), inspect_anonymized_file(), inspect_uploaded_file(), run_anonymize_check_stream(), _auto_detect_columns(), _list_columns(), _load_dataframe(), main() (+15 more)

### Community 7 - "Insight Cache and LLM"
Cohesion: 0.16
Nodes (22): cache_has_full_dashboard_payload(), cache_matches_generation_settings(), load_cache(), save_cache(), get_llm_client(), LLMClient, _cache_filters_match(), _cache_key() (+14 more)

### Community 8 - "Anonymization Quality"
Cohesion: 0.09
Nodes (27): Anonymization Pipeline, Carry-Forward Detection, Late-Masking Methodology, Resumable Chunk Processing, Anonymization Pipeline Improvements, Confidence Score Thresholds, Custom Word Blocklist, German Language Support (+19 more)

### Community 9 - "Retrieval and Reranking"
Cohesion: 0.18
Nodes (25): build_where_filter(), _candidate_metrics(), classification_cache_metadata(), collect_documents_by_query(), collect_theme_documents(), collection_embedding_model(), _combine_where(), current_reranker_id() (+17 more)

### Community 10 - "OpenAI Privacy Filter"
Cohesion: 0.19
Nodes (16): _config_allows(), ensure_openai_privacy_filter_available(), openai_privacy_filter_collect_batch(), openai_privacy_filter_collect_spans(), Batch collect (start, end, tag) per text — same shape as eu_pii_collect_batch., Raise a clear error if the selected OpenAI Privacy Filter layer is unavailable., _spans_tuple_for_text(), _strip_prefix() (+8 more)

### Community 11 - "PII False Positive Checks"
Cohesion: 0.31
Nodes (8): _ask_llm(), _detect_spans(), DataFrame, PII False Positive Checker -------------------------- Reads the original (non-an, Send text + entities to llama3.1:8b and parse the JSON response., Run Presidio + filter and return entity dicts., _read_input(), run()

### Community 12 - "Generation Prompts"
Cohesion: 0.43
Nodes (5): _append_evidence(), build_batch_summary_prompt(), build_prompt(), default_prompt(), parse_llm_json()

### Community 14 - "Vector Query CLI"
Cohesion: 0.67
Nodes (3): main(), Search the vector database.      Args:         query:       Natural language que, search()

### Community 15 - "Frontend Package Metadata"
Cohesion: 0.50
Nodes (3): dependencies, react-router, react-router-dom

## Knowledge Gaps
- **19 isolated node(s):** `react-router`, `react-router-dom`, `DataFrame`, `DataFrame`, `ndarray` (+14 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_model_device()` connect `Embedding Runtime` to `Anonymization Filters`, `Theme Classification`, `OpenAI Privacy Filter`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `ensure_eu_pii_available()` connect `Anonymization Filters` to `Llama Model Configuration`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `LlamaCppClient` connect `Llama Model Configuration` to `Insight Cache and LLM`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **What connects `react-router`, `react-router-dom`, `DataFrame` to the rest of the system?**
  _86 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Anonymization Filters` be split into smaller, more focused modules?**
  _Cohesion score 0.05331510594668489 - nodes in this community are weakly interconnected._
- **Should `Insight Pipeline Flow` be split into smaller, more focused modules?**
  _Cohesion score 0.06025369978858351 - nodes in this community are weakly interconnected._
- **Should `Theme Classification` be split into smaller, more focused modules?**
  _Cohesion score 0.13015873015873017 - nodes in this community are weakly interconnected._