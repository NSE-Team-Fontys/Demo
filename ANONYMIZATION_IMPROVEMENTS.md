# Anonymization Pipeline Improvements

Summary of changes made to the masking quality of the NSE anonymization pipeline.
See `MASKING_TUNING.txt` for guidance on adjusting thresholds when results are still not as expected.

---

## 1. German Language Support

**Problem:** Dutch survey responses sometimes contain German words or sentences. Without a German NLP model, these were processed through the Dutch spaCy model (`nl_core_news_lg`), which has no knowledge of German vocabulary and frequently misidentified German words as person names or locations.

**Changes:**

| File | Change |
|---|---|
| `requirements-common.txt` | Added `de_core_news_lg-3.8.0` wheel |
| `src/pipeline/01_anonymization/layers/layer1_presidio.py` | Added `_SPACY_DE_MODEL` / `_SPACY_DE_WHL` constants |
| `layer1_presidio.py` | `_ensure_spacy_models()` now auto-installs `de_core_news_lg` if missing |
| `layer1_presidio.py` | `_build_analyzer()` registers the German model with Presidio |
| `layer1_presidio.py` | Language detection in `collect_presidio_spans` now accepts `"de"` in addition to `"nl"` and `"en"` |

**Effect:** Text detected as German is now analyzed by `de_core_news_lg`, which correctly identifies German common nouns and avoids tagging them as named entities.

---

## 2. False Positive Reduction

**Problem:** All three tag types (`[NAME]`, `[LOCATION]`, `[PII]`) had significant overfiltering. The NER models were tagging Dutch compound nouns, product names, acronyms, common words, and low-confidence guesses as sensitive entities.

The root causes were:
- NRP (nationality/religion/political) entities incorrectly mapped to `[NAME]` instead of `[PII]`
- No confidence score threshold — low-certainty detections were kept
- No structural validation of span shape — anything the model flagged was kept
- EU-PII transformer was applying the entire column as one batch (OOM + no score filtering)

### 2a. Shared Plausibility Functions

**File:** `src/pipeline/01_anonymization/layers/layer_utils.py`

Three shape-based filter functions added. These are language-agnostic and contain no hardcoded words — they only look at structural properties of the span text.

**`is_plausible_name_span(span_text)`**
Rejects `[NAME]` spans that match any of:
- All-caps ≤ 5 characters → acronym (e.g. `SEO`, `CRO`, `START`)
- Single token > 12 characters → Dutch compound noun (e.g. `Medewerkerstevredenheid`)
- CamelCase single token → product/brand name (e.g. `FeedPulse`)
- Entirely lowercase → common word
- More than 50% digits → number, not a name

**`is_plausible_location_span(span_text)`**
Rejects `[LOCATION]` spans that match any of:
- Single token > 15 characters → Dutch compound noun (threshold higher than names since some place names are longer)
- CamelCase single token → product/platform name (e.g. `YouTube`, `Portflow`)
- All-lowercase single token → common word (e.g. `peer`, `google`, `research`)
- All-caps ≤ 5 characters, no digits → abbreviation (e.g. `START`, `HBO`)
- Single token ending in a digit → team/group identifier (e.g. `Mensen8`)

**`is_plausible_pii_span(span_text)`**
Rejects `[PII]` catch-all spans that match any of:
- CamelCase single token → product/software name (e.g. `ChatGPT`, `NotebookLM`)
- All-lowercase alphabetic single token → common word (e.g. `hulp`, `anders`, `other`)
- All-caps ≤ 4 characters, no digits → short abbreviation (e.g. `HBO`)

Both `layer1_presidio.py` and `layer2_eu_pii.py` import from this shared module. One place to maintain.

### 2b. Presidio Layer (Layer 1)

**File:** `src/pipeline/01_anonymization/layers/layer1_presidio.py`

| Change | Detail |
|---|---|
| **NRP entity → `[PII]`** | Was mapped to `[NAME]`. NRP (Nationality / Religion / Political group) entities are special-category personal data under GDPR Art. 9. In Dutch student surveys these are language/nationality mentions (e.g. `Dutch`, `Nederlands`, `Engelstalig`) — they should be masked but as `[PII]`, not `[NAME]`. |
| **`PRESIDIO_MIN_SCORE` threshold** | Added env-configurable minimum confidence score (default `0.6`). Presidio assigns scores to each detected entity; spans below this threshold are dropped before the plausibility check. Set via `.env`: `PRESIDIO_MIN_SCORE=0.6` |
| **Plausibility check for `[NAME]`** | `collect_presidio_spans` now calls `is_plausible_name_span` on every `[NAME]` span after the score check. |
| **Plausibility check for `[LOCATION]`** | Same score threshold + `is_plausible_location_span` applied to every `[LOCATION]` span. |

### 2c. EU-PII Layer (Layer 2)

**File:** `src/pipeline/01_anonymization/layers/layer2_eu_pii.py`

| Change | Detail |
|---|---|
| **`EU_PII_MIN_SCORE` threshold** | Added env-configurable minimum confidence score (default `0.85`, higher than Presidio because the transformer model is more sensitive). Applied to all spans before any other check. Set via `.env`: `EU_PII_MIN_SCORE=0.85` |
| **Plausibility check for `[PII]`** | `eu_pii_collect_batch` now calls `is_plausible_pii_span` on spans mapped to the `[PII]` catch-all category. |
| **Plausibility check for `[LOCATION]`** | Same check using `is_plausible_location_span` applied to `[LOCATION]` spans. |
| **OOM fix (batch size)** | Both `eu_pii_collect_batch` and `eu_pii_safeguard_anonymize_batch` previously passed the entire column to the HuggingFace pipeline at once (`batch_size=len(texts)`), causing out-of-memory errors on large files. Both now cap at `batch_size=min(len(texts), 128)`. |

### 2d. Filter Chain (end-to-end)

For any detected span, the full filter chain is now:

```
Presidio / EU-PII detects span
    │
    ▼
Score threshold         (PRESIDIO_MIN_SCORE or EU_PII_MIN_SCORE)
    │ passes
    ▼
Shape plausibility      (is_plausible_*_span in layer_utils.py)
    │ passes
    ▼
_filter_spans           (privacy_pipeline.py — dedup, merge, stopwords)
    │ passes
    ▼
apply_all_masks         (longest span wins, no double-masking)
    │
    ▼
Custom word blocklist   (post-processing, see section 3)
```

---

## 3. Custom Word Filter (UI Feature)

**Problem:** Some domain-specific sensitive words are consistently missed by the NER models because they are too uncommon to appear in training data, or are contextually ambiguous. Users needed a way to hardcode specific words that should always be masked, without modifying any pipeline code.

**Design principle:** The blocklist is applied as a post-processing step *after* the full NER pipeline completes, using simple case-insensitive whole-word regex replacement. It has no interaction with the models and does not affect anonymization performance.

**New files and changes:**

| File | Change |
|---|---|
| `src/config/paths.py` | Added `WORD_BLOCKLIST_PATH = DATA_DIR / "word_blocklist.json"` |
| `src/pipeline/01_anonymization/blocklist.py` | **New module.** `load_blocklist()`, `save_blocklist(words)`, `apply_blocklist(text, words)` |
| `src/pipeline/01_anonymization/engine.py` | Blocklist loaded once before the column loop; applied via `apply_blocklist` after each `process_chunk_sync` call |
| `src/api/anonymize_routes.py` | Two new endpoints: `GET /api/word-blocklist` and `POST /api/word-blocklist` |
| `dashboard/src/components/AnonymizerTab.jsx` | New "Custom Word Filter" card in Step 2 |

**How it works:**
- Words/phrases are stored in `data/word_blocklist.json` and persist between runs.
- Matching is case-insensitive and whole-word (`\b` boundaries), so adding `"minor"` will not mask `"administrator"`.
- Multi-word phrases are supported and matched literally.
- Matches are replaced with `[PII]`.
- The list is managed via the UI: type a word, press Enter or click Add, click × to remove. Changes save immediately.

---

## 4. Tooling Improvements

### `run_anon_test.py`
- Added `import src.config.runtime` so `.env` variables (`ANONYMIZE_BATCH_SIZE`, `OMP_NUM_THREADS`, etc.) are loaded before the pipeline starts.
- Added `--verify-only` flag: runs verification on existing `anon_test_output.csv` without re-anonymizing. Useful when the anonymization completed but verification OOM'd or was skipped.
- Added `--verify-sample N` flag: checks only N random rows per column during verification instead of all rows, making verification ~27× faster on large files while still producing representative missed/removed samples.

### `engine.py` (`run_check_stream`)
- Added `sample_rows` parameter to limit verification to a random subset of rows, used by `--verify-sample`.

### `MASKING_TUNING.txt`
- New plain-text guide explaining which thresholds to raise or lower for each symptom, how to identify which layer produced a false positive, how to add new structural rules, and the before/after comparison workflow.
