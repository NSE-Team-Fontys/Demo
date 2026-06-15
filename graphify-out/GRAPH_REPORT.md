# Graph Report - .  (2026-06-14)

## Corpus Check
- 98 files · ~208,567 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 633 nodes · 1094 edges · 54 communities (43 shown, 11 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Embedding Model Runtime|Embedding Model Runtime]]
- [[_COMMUNITY_Anonymization Pipeline|Anonymization Pipeline]]
- [[_COMMUNITY_Local LLM Models|Local LLM Models]]
- [[_COMMUNITY_Anonymization API Routes|Anonymization API Routes]]
- [[_COMMUNITY_Reranker Model Runtime|Reranker Model Runtime]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Retrieval Service|Retrieval Service]]
- [[_COMMUNITY_Retrieval Quality Tests|Retrieval Quality Tests]]
- [[_COMMUNITY_Generation Cache Service|Generation Cache Service]]
- [[_COMMUNITY_Blocklist Anonymization|Blocklist Anonymization]]
- [[_COMMUNITY_Anonymization Service|Anonymization Service]]
- [[_COMMUNITY_EU PII Detection|EU PII Detection]]
- [[_COMMUNITY_Dashboard Theme Data|Dashboard Theme Data]]
- [[_COMMUNITY_Presidio Detection|Presidio Detection]]
- [[_COMMUNITY_Privacy Masking Pipeline|Privacy Masking Pipeline]]
- [[_COMMUNITY_OpenAI Privacy Filter|OpenAI Privacy Filter]]
- [[_COMMUNITY_Insight Detail Views|Insight Detail Views]]
- [[_COMMUNITY_Trend Visualization|Trend Visualization]]
- [[_COMMUNITY_Pipeline Control Tabs|Pipeline Control Tabs]]
- [[_COMMUNITY_Dashboard Navigation State|Dashboard Navigation State]]
- [[_COMMUNITY_Dashboard Hero Locations|Dashboard Hero Locations]]
- [[_COMMUNITY_Dashboard API Integration|Dashboard API Integration]]
- [[_COMMUNITY_LLM Client Tests|LLM Client Tests]]
- [[_COMMUNITY_Theme Classification Tests|Theme Classification Tests]]
- [[_COMMUNITY_Theme Visualizations|Theme Visualizations]]
- [[_COMMUNITY_Generation Prompts|Generation Prompts]]
- [[_COMMUNITY_External Platform Icons|External Platform Icons]]
- [[_COMMUNITY_Theme Detail Data|Theme Detail Data]]
- [[_COMMUNITY_Anonymization Checkpoints|Anonymization Checkpoints]]
- [[_COMMUNITY_Vector Query CLI|Vector Query CLI]]
- [[_COMMUNITY_Layered Hero Artwork|Layered Hero Artwork]]
- [[_COMMUNITY_Vite Branding|Vite Branding]]
- [[_COMMUNITY_Dashboard Entry Shell|Dashboard Entry Shell]]
- [[_COMMUNITY_Model Cleanup Tests|Model Cleanup Tests]]
- [[_COMMUNITY_Application Favicon|Application Favicon]]
- [[_COMMUNITY_Embedding Stage Package|Embedding Stage Package]]
- [[_COMMUNITY_Retrieval Stage Package|Retrieval Stage Package]]
- [[_COMMUNITY_Generation Stage Package|Generation Stage Package]]
- [[_COMMUNITY_React Branding|React Branding]]
- [[_COMMUNITY_Configuration Package|Configuration Package]]
- [[_COMMUNITY_Anonymization Layer Package|Anonymization Layer Package]]
- [[_COMMUNITY_Pipeline Package|Pipeline Package]]
- [[_COMMUNITY_Utility Package|Utility Package]]

## God Nodes (most connected - your core abstractions)
1. `LlamaCppClient` - 21 edges
2. `get_model_device()` - 20 edges
3. `build_vector_db_stream()` - 18 edges
4. `build_vector_db()` - 16 edges
5. `process_file_with_layers()` - 15 edges
6. `describe_model_device()` - 15 edges
7. `collect_presidio_spans()` - 13 edges
8. `eu_pii_collect_batch()` - 13 edges
9. `detect_sep()` - 13 edges
10. `PersistedThemeRetrievalTests` - 12 edges

## Surprising Connections (you probably didn't know these)
- `create_app()` --calls--> `register_blueprints()`  [EXTRACTED]
  app.py → src/api/__init__.py
- `process_file_with_layers()` --calls--> `Path`  [INFERRED]
  src/pipeline/01_anonymization/engine.py → src/utils/file_parsers.py
- `Span` --uses--> `Span`  [INFERRED]
  src/pipeline/01_anonymization/layers/layer2_openai_privacy_filter.py → src/pipeline/01_anonymization/layers/layer_utils.py
- `get_theme_embedding_model()` --calls--> `describe_embedding_runtime()`  [INFERRED]
  src/pipeline/03_retrieval/service.py → src/pipeline/02_embedding/embedding_models.py
- `get_theme_embedding_model()` --calls--> `load_embedding_model()`  [INFERRED]
  src/pipeline/03_retrieval/service.py → src/pipeline/02_embedding/embedding_models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Survey Insight Pipeline Flow** — 01_anonymization_readme_anonymization_pipeline, 02_embedding_readme_embedding_pipeline, 03_retrieval_readme_retrieval_pipeline, 04_generation_readme_insight_generation_pipeline [INFERRED 0.95]
- **Persisted Theme Evidence Flow** — 02_embedding_readme_persisted_theme_classification, 03_retrieval_readme_persisted_dashboard_theme_evidence, 04_generation_readme_semantic_theme_evidence_selection [EXTRACTED 1.00]
- **Shared Hardware Acceleration Routing** — utils_readme_model_device, 02_embedding_readme_embedding_models, 03_retrieval_readme_reranker_models [EXTRACTED 1.00]
- **External Platform Logos** — public_icons_bluesky_icon, public_icons_discord_icon, public_icons_github_icon, public_icons_x_icon [INFERRED 0.85]
- **Layered System Composition** — assets_hero_stacked_layers, assets_hero_layer_connection, assets_hero_core_module [INFERRED 0.85]

## Communities (54 total, 11 thin omitted)

### Community 0 - "Embedding Model Runtime"
Cohesion: 0.09
Nodes (37): describe_embedding_runtime(), _downloads_disabled(), load_embedding_model(), _load_embedding_model_cached(), Load a SentenceTransformer embedding model on the preferred local device.      W, Release cached embedding models and return unused accelerator memory., _trust_remote_code_enabled(), unload_embedding_models() (+29 more)

### Community 1 - "Anonymization Pipeline"
Cohesion: 0.05
Nodes (48): Anonymization Pipeline, Carry-forward Detection, Anonymization Checkpoints, Anonymization Engine, Late-Masking Methodology, PII Detection Layers, Privacy Pipeline, Anonymization Reporting (+40 more)

### Community 2 - "Local LLM Models"
Cohesion: 0.10
Nodes (11): llama_cpp_model_options(), LlamaCppGenerationSettings, LlamaCppModel, resolve_llama_cpp_model(), get_llm_client(), LlamaCppClient, LLMClient, LocalModelConnectionError (+3 more)

### Community 3 - "Anonymization API Routes"
Cohesion: 0.07
Nodes (11): register_blueprints(), _build_filter_grid(), _filters_from_payload(), precompute_insights(), precompute_preview(), Return cross-product size for the given filter dimensions., Expand the cross-product of the requested filter dimensions., theme_summary() (+3 more)

### Community 4 - "Reranker Model Runtime"
Cohesion: 0.12
Nodes (23): describe_reranker_runtime(), _downloads_disabled(), load_reranker_model(), _load_reranker_model_cached(), Release cached cross-encoders and unused accelerator memory., reranker_enabled(), selected_reranker_model(), _trust_remote_code_enabled() (+15 more)

### Community 5 - "Frontend Dependencies"
Cohesion: 0.07
Nodes (27): dependencies, framer-motion, react, react-dom, react-router-dom, devDependencies, autoprefixer, eslint (+19 more)

### Community 6 - "Retrieval Service"
Cohesion: 0.18
Nodes (24): build_where_filter(), _candidate_metrics(), classification_cache_metadata(), collect_documents_by_query(), collect_theme_documents(), collection_embedding_model(), _combine_where(), expected_classification_config() (+16 more)

### Community 7 - "Retrieval Quality Tests"
Cohesion: 0.09
Nodes (5): _assignment(), FakeEmbeddingModel, FakeLlmClient, FakeReranker, PersistedThemeRetrievalTests

### Community 8 - "Generation Cache Service"
Cohesion: 0.23
Nodes (19): cache_has_full_dashboard_payload(), cache_matches_generation_settings(), load_cache(), save_cache(), _cache_filters_match(), _cache_key(), _cached_dashboard_response(), _document_batches() (+11 more)

### Community 9 - "Blocklist Anonymization"
Cohesion: 0.15
Nodes (15): apply_blocklist(), load_blocklist(), Return the current custom word blocklist, or [] if none saved., Persist the blocklist to disk, deduplicating and stripping whitespace., Replace every whole-word (case-insensitive) occurrence of each blocklist     ent, save_blocklist(), process_file_with_layers(), Run only the verification step on already-existing original + anonymized files. (+7 more)

### Community 10 - "Anonymization Service"
Cohesion: 0.24
Nodes (14): _read_input(), anonymize_uploaded_file(), inspect_anonymized_file(), inspect_uploaded_file(), run_anonymize_check_stream(), Path, DataFrame, AppStartupTests (+6 more)

### Community 11 - "EU PII Detection"
Cohesion: 0.17
Nodes (17): _apply_entities(), _config_allows_tag(), ensure_eu_pii_available(), eu_pii_collect_batch(), eu_pii_safeguard_anonymize(), eu_pii_safeguard_anonymize_batch(), _eu_pii_tag(), _is_numeric_or_id() (+9 more)

### Community 12 - "Dashboard Theme Data"
Cohesion: 0.13
Nodes (14): AI_SUMMARIES, applyModifiers(), BASE_THEMES, clamp(), COHORT_MODIFIERS, COMPARISON_DATA, COMPARISON_LABELS, JAAR_MODIFIERS (+6 more)

### Community 13 - "Presidio Detection"
Cohesion: 0.17
Nodes (17): AnalyzerEngine, anonymize_with_presidio(), _build_analyzer(), build_presidio_operators(), ensure_presidio_available(), _ensure_spacy_models(), _get_analyzer(), presidio_masking_spec() (+9 more)

### Community 14 - "Privacy Masking Pipeline"
Cohesion: 0.18
Nodes (17): unload_models(), unload_models(), unload_models(), extend_name_spans_for_tussenvoegsels(), Extend [NAME] spans to include following Dutch tussenvoegsels and surnames., apply_all_masks(), _build_carryforward_spans(), _canonical_name_for_carryforward() (+9 more)

### Community 15 - "OpenAI Privacy Filter"
Cohesion: 0.19
Nodes (16): _config_allows(), ensure_openai_privacy_filter_available(), openai_privacy_filter_collect_batch(), openai_privacy_filter_collect_spans(), Batch collect (start, end, tag) per text — same shape as eu_pii_collect_batch., Raise a clear error if the selected OpenAI Privacy Filter layer is unavailable., _spans_tuple_for_text(), _strip_prefix() (+8 more)

### Community 16 - "Insight Detail Views"
Cohesion: 0.14
Nodes (6): FilterDropdown(), buildInsightCards(), CommentCard(), INSIGHT_STOPWORDS, normaliseComment(), summaryPoints()

### Community 17 - "Trend Visualization"
Cohesion: 0.14
Nodes (9): buildArea(), buildPath(), PAD, TrendChart(), FILTER_OPTIONS, OPLEIDING_PROFILES, YEARS, BADGE (+1 more)

### Community 18 - "Pipeline Control Tabs"
Cohesion: 0.22
Nodes (7): AnonymizerTab(), InsightGenerator(), QueryTab(), AVAILABLE_MODELS, VectorDBBuilder(), AVAILABLE_LLM_MODELS, PipelineDemo()

### Community 19 - "Dashboard Navigation State"
Cohesion: 0.22
Nodes (9): NavBar(), useVectorDB(), VectorDBContext, VectorDBProvider(), useApiData(), Overview(), ThemeDetail(), Vergelijken() (+1 more)

### Community 20 - "Dashboard Hero Locations"
Cohesion: 0.24
Nodes (7): HeroBanner(), SubthemeWordCloud(), BRIN_TO_CITY, CITY_TO_BRIN, LOCATION_OPTIONS, getFilteredThemes(), mergeWithLiveData()

### Community 21 - "Dashboard API Integration"
Cohesion: 0.36
Nodes (8): API_TO_DASHBOARD, apiFetch(), checkHealth(), DYNAMIC_THEME_META, fetchCompare(), fetchSentiment(), fetchThemes(), filtersToParams()

### Community 23 - "Theme Classification Tests"
Cohesion: 0.24
Nodes (3): BuildEmbeddingModel, ScoreReranker, ThemeClassificationTests

### Community 24 - "Theme Visualizations"
Cohesion: 0.31
Nodes (4): ThemeCard(), getThemeColor(), THEME_COLOR_LIST, THEME_COLORS

### Community 25 - "Generation Prompts"
Cohesion: 0.43
Nodes (5): _append_evidence(), build_batch_summary_prompt(), build_prompt(), default_prompt(), parse_llm_json()

### Community 26 - "External Platform Icons"
Cohesion: 0.48
Nodes (7): Bluesky Icon, Discord Icon, Documentation Icon, GitHub Icon, Icon Sprite Sheet, Social Profile Icon, X Icon

### Community 27 - "Theme Detail Data"
Cohesion: 0.53
Nodes (4): DetailDrawer(), buildApiFilters(), useThemeSummary(), ViewMorePage()

### Community 29 - "Vector Query CLI"
Cohesion: 0.67
Nodes (3): main(), Search the vector database.      Args:         query:       Natural language que, search()

### Community 30 - "Layered Hero Artwork"
Cohesion: 0.50
Nodes (4): Core Module, Layered Platform Hero Illustration, Inter-Layer Connection, Stacked Digital Layers

### Community 31 - "Vite Branding"
Cohesion: 0.50
Nodes (4): Adaptive Color Scheme, Lightning Bolt, Vite, Vite Logo

### Community 32 - "Dashboard Entry Shell"
Cohesion: 0.50
Nodes (4): Google Fonts, main.jsx Application Entry, NSE Insights Dashboard Shell, Root Application Mount Point

### Community 34 - "Application Favicon"
Cohesion: 0.67
Nodes (3): Lightning Bolt Symbol, Purple and Cyan Glow Palette, Stylized Lightning Bolt Favicon

## Knowledge Gaps
- **66 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+61 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_model_device()` connect `Reranker Model Runtime` to `Embedding Model Runtime`, `Blocklist Anonymization`, `EU PII Detection`, `Presidio Detection`, `OpenAI Privacy Filter`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `Path` connect `Anonymization Service` to `Blocklist Anonymization`, `Local LLM Models`, `Theme Classification Tests`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `RuntimeError` (e.g. with `classify_theme_batch()` and `_validate_classified_collection()`) actually correct?**
  _`RuntimeError` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _121 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Embedding Model Runtime` be split into smaller, more focused modules?**
  _Cohesion score 0.08563134978229318 - nodes in this community are weakly interconnected._
- **Should `Anonymization Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.051418439716312055 - nodes in this community are weakly interconnected._
- **Should `Local LLM Models` be split into smaller, more focused modules?**
  _Cohesion score 0.09988385598141696 - nodes in this community are weakly interconnected._