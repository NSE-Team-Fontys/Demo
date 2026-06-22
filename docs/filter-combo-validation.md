# Filter Combination Validation

## Problem

The precompute grid is the cross-product of all selected filter dimensions (e.g. academic_year × location × programme). This can produce hundreds or thousands of combinations, many of which have zero matching documents (e.g. HBO-ICT does not exist in Rotterdam). Without validation:

- The LLM is called for empty filter sets, wasting time and producing bad output.
- The combo count displayed in the UI is inflated (naive cross-product).
- The progress bar overestimates total work.

## Solution

One bulk ChromaDB metadata fetch is performed before the precompute loop starts. An inverted index is built per filter dimension, then each combo is validated Python-side using set intersection. Only combos with ≥1 matching document are kept.

```
N combos × 1 ChromaDB call  →  1 ChromaDB call + N Python set intersections
```

For 8000 combos this reduces ChromaDB round-trips from 8000 to 1.

## Where it lives

| File | What it does |
|------|--------------|
| `src/pipeline/03_retrieval/service.py` | `filter_valid_combos(combos)` — bulk fetch + inverted index + intersection |
| `src/pipeline/04_generation/service.py` | Calls `filter_valid_combos` at stream start; uses `valid_grid` in the loop |
| `src/api/insight_routes.py` | `/api/precompute-preview` returns `valid_combos` alongside naive `combos` count |
| `dashboard/src/components/InsightGenerator.jsx` | Fetches preview on dimension change; displays `valid_combos` in UI |

## Data flow

```
User selects filter dimensions
        ↓
InsightGenerator fetches /api/precompute-preview
        ↓
Backend builds cross-product → filter_valid_combos() → returns valid_combos count
        ↓
UI shows accurate combo count + time estimate
        ↓
User starts precompute
        ↓
precompute_insights_stream:
  1. filter_valid_combos(normalized_grid)  ← one ChromaDB call
  2. total_steps based on valid_grid length  ← accurate progress bar
  3. loop over valid_grid only  ← no empty LLM calls
```

## Performance

- `filter_valid_combos` fetches all metadata once (`include=["metadatas"]`, no embeddings or documents).
- Inverted index build: O(docs × dimensions).
- Per-combo check: O(dimensions) set intersection, short-circuits on first empty set.
- Typical cost: <1 second for datasets up to ~10k documents.
