# Graph Report - .  (2026-06-12)

## Corpus Check
- 85 files · ~52,358 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 525 nodes · 869 edges · 43 communities (31 shown, 12 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 82 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Backend API Routes|Backend API Routes]]
- [[_COMMUNITY_Configuration Package|Configuration Package]]
- [[_COMMUNITY_Anonymization Engine|Anonymization Engine]]
- [[_COMMUNITY_Checkpoint Persistence|Checkpoint Persistence]]
- [[_COMMUNITY_Anonymization Layers Package|Anonymization Layers Package]]
- [[_COMMUNITY_Presidio PII Detection|Presidio PII Detection]]
- [[_COMMUNITY_Span Masking Pipeline|Span Masking Pipeline]]
- [[_COMMUNITY_Embedding Device Runtime|Embedding Device Runtime]]
- [[_COMMUNITY_EU PII Safeguard|EU PII Safeguard]]
- [[_COMMUNITY_OpenAI Privacy Filter|OpenAI Privacy Filter]]
- [[_COMMUNITY_Upload and Anonymization Service|Upload and Anonymization Service]]
- [[_COMMUNITY_Embedding Package|Embedding Package]]
- [[_COMMUNITY_Retrieval Package|Retrieval Package]]
- [[_COMMUNITY_Vector Search CLI|Vector Search CLI]]
- [[_COMMUNITY_Retrieval and Reranking|Retrieval and Reranking]]
- [[_COMMUNITY_Generation Package|Generation Package]]
- [[_COMMUNITY_Insight Cache and LLM Clients|Insight Cache and LLM Clients]]
- [[_COMMUNITY_llama.cpp Generation Runtime|llama.cpp Generation Runtime]]
- [[_COMMUNITY_Insight Prompt Construction|Insight Prompt Construction]]
- [[_COMMUNITY_Pipeline Package|Pipeline Package]]
- [[_COMMUNITY_Utilities Package|Utilities Package]]
- [[_COMMUNITY_Pipeline Architecture Concepts|Pipeline Architecture Concepts]]
- [[_COMMUNITY_Frontend Toolchain|Frontend Toolchain]]
- [[_COMMUNITY_Dashboard Views and Charts|Dashboard Views and Charts]]
- [[_COMMUNITY_Pipeline Demo UI|Pipeline Demo UI]]
- [[_COMMUNITY_Filters and Theme Details|Filters and Theme Details]]
- [[_COMMUNITY_Privacy and GDPR Model|Privacy and GDPR Model]]
- [[_COMMUNITY_Application Branding|Application Branding]]
- [[_COMMUNITY_Bluesky and X Icons|Bluesky and X Icons]]
- [[_COMMUNITY_Discord Social Icon|Discord Social Icon]]
- [[_COMMUNITY_Docs and GitHub Icons|Docs and GitHub Icons]]
- [[_COMMUNITY_Layered Hero Illustration|Layered Hero Illustration]]
- [[_COMMUNITY_React Branding|React Branding]]
- [[_COMMUNITY_Vite Branding|Vite Branding]]

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

## Communities (43 total, 12 thin omitted)

### Community 7 - "Backend API Routes"
Cohesion: 0.08
Nodes (5): theme_summary(), precompute_insights(), _filters_from_payload(), query_vectors(), _filters_from_args()

### Community 29 - "Anonymization Engine"
Cohesion: 0.15
Nodes (18): Stage 01: PII anonymization and privacy filters., load_blocklist(), save_blocklist(), apply_blocklist(), Return the current custom word blocklist, or [] if none saved., Persist the blocklist to disk, deduplicating and stripping whitespace., Replace every whole-word (case-insensitive) occurrence of each blocklist     ent, _read_input() (+10 more)

### Community 8 - "Presidio PII Detection"
Cohesion: 0.14
Nodes (23): _spacy_model_installed(), _ensure_spacy_models(), _build_analyzer(), AnalyzerEngine, _get_analyzer(), register_custom_presidio_recognizers(), build_presidio_operators(), ensure_presidio_available() (+15 more)

### Community 31 - "Span Masking Pipeline"
Cohesion: 0.21
Nodes (15): unload_models(), unload_models(), unload_models(), extend_spans_for_original(), _is_plausible_name_span(), apply_all_masks(), _build_carryforward_spans(), _canonical_name_for_carryforward() (+7 more)

### Community 3 - "Embedding Device Runtime"
Cohesion: 0.11
Nodes (28): _init_spacy_device(), Activate the same device that get_model_device() picked for the rest     of the, _trust_remote_code_enabled(), describe_embedding_runtime(), _downloads_disabled(), _load_embedding_model_cached(), SentenceTransformer, load_embedding_model() (+20 more)

### Community 33 - "EU PII Safeguard"
Cohesion: 0.22
Nodes (11): _is_numeric_or_id(), _eu_pii_tag(), _config_allows_tag(), _apply_entities(), eu_pii_safeguard_anonymize(), eu_pii_safeguard_anonymize_batch(), Return True if the span is a number, phone number, or alphanumeric ID (e.g. 2870, Layer 2 masking (no span plumbing): returns text with tags. (+3 more)

### Community 30 - "OpenAI Privacy Filter"
Cohesion: 0.19
Nodes (16): ensure_openai_privacy_filter_available(), _strip_prefix(), _tag(), _config_allows(), _spans_tuple_for_text(), openai_privacy_filter_collect_batch(), openai_privacy_filter_collect_spans(), Span (+8 more)

### Community 9 - "Upload and Anonymization Service"
Cohesion: 0.29
Nodes (11): inspect_uploaded_file(), anonymize_uploaded_file(), inspect_anonymized_file(), run_anonymize_check_stream(), get_upload_path(), save_uploaded_file(), Path, read_dataframe() (+3 more)

### Community 13 - "Vector Search CLI"
Cohesion: 0.67
Nodes (3): search(), main(), Search the vector database.      Args:         query:       Natural language que

### Community 5 - "Retrieval and Reranking"
Cohesion: 0.14
Nodes (29): _downloads_disabled(), _trust_remote_code_enabled(), reranker_enabled(), selected_reranker_model(), describe_reranker_runtime(), _load_reranker_model_cached(), CrossEncoder, load_reranker_model() (+21 more)

### Community 6 - "Insight Cache and LLM Clients"
Cohesion: 0.16
Nodes (21): load_cache(), save_cache(), cache_matches_generation_settings(), cache_has_full_dashboard_payload(), LLMClient, Protocol, get_llm_client(), _model_generation_settings() (+13 more)

### Community 2 - "llama.cpp Generation Runtime"
Cohesion: 0.12
Nodes (8): LlamaCppGenerationSettings, Any, LlamaCppModel, resolve_llama_cpp_model(), llama_cpp_model_options(), LocalModelConnectionError, RuntimeError, LlamaCppClient

### Community 11 - "Insight Prompt Construction"
Cohesion: 0.40
Nodes (3): default_prompt(), build_prompt(), parse_llm_json()

### Community 4 - "Pipeline Architecture Concepts"
Cohesion: 0.06
Nodes (41): Central Pipeline Configuration, Path Management, Runtime Environment Initialization, Runtime Settings, Theme Taxonomy, Metadata Alias Mapping, Generation Cache Binding, Anonymization Pipeline (+33 more)

### Community 28 - "Frontend Toolchain"
Cohesion: 0.07
Nodes (27): name, private, version, type, scripts, dev, build, lint (+19 more)

### Community 27 - "Dashboard Views and Charts"
Cohesion: 0.06
Nodes (30): App(), ComparisonMiniChart(), NavBar(), ThemeCard(), PAD, buildPath(), buildArea(), TrendChart() (+22 more)

### Community 32 - "Pipeline Demo UI"
Cohesion: 0.22
Nodes (7): AnonymizerTab(), InsightGenerator(), QueryTab(), AVAILABLE_MODELS, VectorDBBuilder(), AVAILABLE_LLM_MODELS, PipelineDemo()

### Community 1 - "Filters and Theme Details"
Cohesion: 0.15
Nodes (10): DetailDrawer(), FilterDropdown(), BRIN_TO_CITY, CITY_TO_BRIN, LOCATION_OPTIONS, buildApiFilters(), useThemeSummary(), normaliseComment() (+2 more)

### Community 0 - "Privacy and GDPR Model"
Cohesion: 0.07
Nodes (39): NSE Insights, Privacy-First AI - NSE Deck, 15,000+ Sensitive Open Responses, Anonymize First, Analyze Locally, Aggregate Only, Three-Layer Anonymization Engine, Standard PII Removal, EU-Specific Identifier Removal, Contextual Clue Scrubbing (+31 more)

### Community 35 - "Application Branding"
Cohesion: 0.50
Nodes (4): Purple Lightning Bolt Favicon, Lightning Bolt Symbol, Purple Cyan Neon Gradient, Application Brand Identity

### Community 10 - "Bluesky and X Icons"
Cohesion: 0.67
Nodes (3): Bluesky Icon, Bluesky Clip Path, X Icon

### Community 34 - "Layered Hero Illustration"
Cohesion: 0.47
Nodes (6): Layered Interface Illustration, Upper Floating Panel, Lower Illuminated Base, Vertical Dotted Connectors, Central White Slot, Layered System Architecture

## Knowledge Gaps
- **73 isolated node(s):** `DataFrame`, `Path Management`, `Runtime Environment Initialization`, `Single-Pass Text Substitution`, `Carry-Forward Detection` (+68 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `process_file_with_layers()` connect `Anonymization Engine` to `Presidio PII Detection`, `Upload and Anonymization Service`, `Embedding Device Runtime`, `Span Masking Pipeline`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `get_model_device()` connect `Embedding Device Runtime` to `Retrieval and Reranking`, `Anonymization Engine`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `LlamaCppClient` connect `llama.cpp Generation Runtime` to `Insight Cache and LLM Clients`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `process_file_with_layers()` (e.g. with `Path` and `detect_sep()`) actually correct?**
  _`process_file_with_layers()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `get_model_device()` (e.g. with `process_file_with_layers()` and `_init_spacy_device()`) actually correct?**
  _`get_model_device()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Static application configuration.`, `Stage 01: PII anonymization and privacy filters.`, `Return the current custom word blocklist, or [] if none saved.` to the rest of the system?**
  _120 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Backend API Routes` be split into smaller, more focused modules?**
  _Cohesion score 0.08262108262108261 - nodes in this community are weakly interconnected._