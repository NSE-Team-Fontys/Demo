# Graph Report - .  (2026-06-12)

## Corpus Check
- Corpus is ~31,268 words - fits in a single context window. You may not need a graph.

## Summary
- 180 nodes · 237 edges · 18 communities (14 shown, 4 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.87)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Privacy-First NSE Concepts|Privacy-First NSE Concepts]]
- [[_COMMUNITY_Reusable UI Components|Reusable UI Components]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Comparison Data Flow|Comparison Data Flow]]
- [[_COMMUNITY_Navigation and Context|Navigation and Context]]
- [[_COMMUNITY_Theme Trend Views|Theme Trend Views]]
- [[_COMMUNITY_Pipeline Demo Controls|Pipeline Demo Controls]]
- [[_COMMUNITY_Layered Hero Illustration|Layered Hero Illustration]]
- [[_COMMUNITY_GDPR Breach Risks|GDPR Breach Risks]]
- [[_COMMUNITY_Application Branding|Application Branding]]
- [[_COMMUNITY_Bluesky and X Icons|Bluesky and X Icons]]
- [[_COMMUNITY_React Branding|React Branding]]
- [[_COMMUNITY_Vite Branding|Vite Branding]]
- [[_COMMUNITY_Discord Social Icon|Discord Social Icon]]
- [[_COMMUNITY_Docs and GitHub Icons|Docs and GitHub Icons]]

## God Nodes (most connected - your core abstractions)
1. `Privacy-First AI - NSE Deck` - 8 edges
2. `useThemeSummary()` - 6 edges
3. `Three-Layer Anonymization Engine` - 6 edges
4. `Protecting Student Voices - NSE Privacy and Access Model` - 6 edges
5. `Controlled Privacy System` - 6 edges
6. `Student Data Hosting Policy` - 6 edges
7. `scripts` - 5 edges
8. `useApiData()` - 5 edges
9. `Anonymize First, Analyze Locally, Aggregate Only` - 5 edges
10. `CITY_TO_BRIN` - 4 edges

## Surprising Connections (you probably didn't know these)
- `NSE Insights` --conceptually_related_to--> `Privacy-First AI - NSE Deck`  [INFERRED]
  dashboard/index.html → dashboard/public/NSE Deck.html
- `NSE Insights` --conceptually_related_to--> `Protecting Student Voices - NSE Privacy and Access Model`  [INFERRED]
  dashboard/index.html → dashboard/public/presentation.html
- `Privacy-First AI - NSE Deck` --semantically_similar_to--> `Protecting Student Voices - NSE Privacy and Access Model`  [INFERRED] [semantically similar]
  dashboard/public/NSE Deck.html → dashboard/public/presentation.html
- `Anonymize First, Analyze Locally, Aggregate Only` --semantically_similar_to--> `Controlled Privacy System`  [INFERRED] [semantically similar]
  dashboard/public/NSE Deck.html → dashboard/public/presentation.html
- `Contextual Clue Scrubbing` --semantically_similar_to--> `Contextual Description Removal`  [INFERRED] [semantically similar]
  dashboard/public/NSE Deck.html → dashboard/public/presentation.html

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Privacy-First Insight Pipeline** — public_nse_deck_three_layer_anonymization, public_nse_deck_local_compute, public_nse_deck_pattern_recognition, public_nse_deck_k_anonymous_aggregated_insight [EXTRACTED 1.00]
- **Controlled Student Feedback Access Model** — public_presentation_data_minimization, public_presentation_k_anonymity_threshold_10, public_presentation_internal_fontys_processing, public_presentation_researcher_aggregated_access [EXTRACTED 1.00]
- **Shared NSE Privacy Architecture** — public_nse_deck_privacy_first_local_analysis, public_presentation_controlled_privacy_system, public_presentation_hosting_policy [INFERRED 0.85]
- **External Social and Developer Destination Icons** — public_icons_bluesky_icon, public_icons_discord_icon, public_icons_github_icon, public_icons_x_icon [INFERRED 0.85]

## Communities (18 total, 4 thin omitted)

### Community 0 - "Privacy-First NSE Concepts"
Cohesion: 0.08
Nodes (33): NSE Insights, Contextual Clue Scrubbing, EU-Specific Identifier Removal, GDPR, K-Anonymity, K-Anonymous Aggregated Insight, Local Compute, Local Language Model (+25 more)

### Community 1 - "Reusable UI Components"
Cohesion: 0.11
Nodes (13): ComparisonMiniChart(), DetailDrawer(), FilterDropdown(), ThemeCard(), BRIN_TO_CITY, CITY_TO_BRIN, LOCATION_OPTIONS, buildApiFilters() (+5 more)

### Community 2 - "Frontend Dependencies"
Cohesion: 0.07
Nodes (27): dependencies, framer-motion, react, react-dom, react-router-dom, devDependencies, autoprefixer, eslint (+19 more)

### Community 3 - "Comparison Data Flow"
Cohesion: 0.19
Nodes (11): useApiData(), THEME_KEYS, Vergelijken(), API_TO_DASHBOARD, apiFetch(), checkHealth(), DYNAMIC_THEME_META, fetchCompare() (+3 more)

### Community 4 - "Navigation and Context"
Cohesion: 0.19
Nodes (9): NavBar(), useVectorDB(), VectorDBContext, VectorDBProvider(), DECK_HTML, NSEDeck(), Overview(), Presentatie() (+1 more)

### Community 5 - "Theme Trend Views"
Cohesion: 0.16
Nodes (7): buildArea(), buildPath(), PAD, TrendChart(), BADGE, BADGE_LABEL, ThemeDetail()

### Community 6 - "Pipeline Demo Controls"
Cohesion: 0.22
Nodes (7): AnonymizerTab(), InsightGenerator(), QueryTab(), AVAILABLE_MODELS, VectorDBBuilder(), AVAILABLE_LLM_MODELS, PipelineDemo()

### Community 7 - "Layered Hero Illustration"
Cohesion: 0.47
Nodes (6): Central White Slot, Layered Interface Illustration, Layered System Architecture, Lower Illuminated Base, Upper Floating Panel, Vertical Dotted Connectors

### Community 8 - "GDPR Breach Risks"
Cohesion: 0.33
Nodes (6): 72-Hour Breach Notification, Current Uncontrolled Student Feedback Flow, Dutch Data Protection Authority, GDPR Article 33, GDPR Article 83, Public AI Tools

### Community 9 - "Application Branding"
Cohesion: 0.50
Nodes (4): Application Brand Identity, Purple Lightning Bolt Favicon, Lightning Bolt Symbol, Purple Cyan Neon Gradient

### Community 10 - "Bluesky and X Icons"
Cohesion: 0.67
Nodes (3): Bluesky Clip Path, Bluesky Icon, X Icon

## Knowledge Gaps
- **64 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+59 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Protecting Student Voices - NSE Privacy and Access Model` connect `Privacy-First NSE Concepts` to `GDPR Breach Risks`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Privacy-First AI - NSE Deck` (e.g. with `NSE Insights` and `Protecting Student Voices - NSE Privacy and Access Model`) actually correct?**
  _`Privacy-First AI - NSE Deck` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Protecting Student Voices - NSE Privacy and Access Model` (e.g. with `NSE Insights` and `Privacy-First AI - NSE Deck`) actually correct?**
  _`Protecting Student Voices - NSE Privacy and Access Model` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _64 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Privacy-First NSE Concepts` be split into smaller, more focused modules?**
  _Cohesion score 0.08143939393939394 - nodes in this community are weakly interconnected._
- **Should `Reusable UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.11083743842364532 - nodes in this community are weakly interconnected._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._