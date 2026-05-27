import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.core.layers.privacy_pipeline import process_chunk_sync, validate_selected_layers

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Chunk size for span collection + masking (Layer 2 HF batching).
# Default 512 for betere throughput; override via ANONYMIZE_BATCH_SIZE indien nodig.
_ANON_BATCH = int(os.environ.get("ANONYMIZE_BATCH_SIZE", "512"))

CHECKPOINT_CSV = Path("data/anon_checkpoint.csv")
CHECKPOINT_META = Path("data/anon_checkpoint_meta.json")
REPORT_FILE = Path("data/anonymization_report.txt")
REPORT_JSON = Path("data/anonymization_report.json")


def _write_report(
    input_path: str,
    output_path: str,
    columns: list,
    layers: list,
    total_rows: int,
    total_cells: int,
    affected_cells: int,
    total_entities: int,
    tag_counts: dict,
    missed_counts: dict,
    missed_samples: dict,
    removed_samples: dict,
) -> None:
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"Anonymization Report — {ts}")
    lines.append("=" * 60)
    lines.append(f"Input file   : {input_path}")
    lines.append(f"Output file  : {output_path}")
    lines.append(f"Layers used  : {', '.join(layers)}")
    lines.append(f"Columns      : {', '.join(columns)}")
    lines.append(f"Rows         : {total_rows}")
    lines.append("")
    lines.append("--- Detection summary ---")
    lines.append(f"Cells scanned   : {total_cells}")
    lines.append(f"Cells affected  : {affected_cells}  ({100 * affected_cells / total_cells:.1f}%)" if total_cells else f"Cells affected  : {affected_cells}")
    lines.append(f"Entities masked : {total_entities}")
    lines.append("")
    lines.append("Tag breakdown:")
    for tag, count in tag_counts.items():
        lines.append(f"  [{tag}]  {count}")
    lines.append("")
    lines.append("--- Verification (Presidio re-scan on original) ---")
    lines.append("Entities still present in output (potential misses):")
    any_missed = False
    for tag, count in missed_counts.items():
        if count:
            any_missed = True
            lines.append(f"  [{tag}]  {count} possibly missed:")
            for s in missed_samples.get(tag, []):
                lines.append(f"    - {s}")
    if not any_missed:
        lines.append("  (none)")
    lines.append("")
    lines.append("Entities successfully removed:")
    for tag, samples in removed_samples.items():
        if samples:
            lines.append(f"  [{tag}]  {len(samples)} unique:")
            for s in samples:
                lines.append(f"    - {s}")
    lines.append("")
    try:
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
        stats_payload = {
            "timestamp": ts,
            "input_path": input_path,
            "output_path": output_path,
            "layers": layers,
            "columns": columns,
            "rows_processed": total_rows,
            "total_cells": total_cells,
            "affected_cells": affected_cells,
            "total_entities": total_entities,
            "tag_counts": tag_counts,
            "missed_counts": missed_counts,
            "missed_samples": missed_samples,
            "removed_samples": removed_samples,
        }
        REPORT_JSON.write_text(json.dumps(stats_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[REPORT] Saved to {REPORT_FILE} and {REPORT_JSON}")
    except Exception as e:
        print(f"[REPORT] Warning: could not save report: {e}")


def _load_checkpoint(input_path: str, sep: str):
    """Return (df, meta) if a valid checkpoint exists for the given input file, else (None, None)."""
    if not CHECKPOINT_CSV.exists() or not CHECKPOINT_META.exists():
        return None, None
    try:
        stat = os.stat(input_path)
        meta = json.loads(CHECKPOINT_META.read_text(encoding="utf-8"))
        if meta.get("input_size") != stat.st_size:
            return None, None
        if abs(meta.get("input_mtime", 0) - stat.st_mtime) > 2:
            return None, None
        df = pd.read_csv(str(CHECKPOINT_CSV), sep=sep, encoding="utf-8-sig")
        return df, meta
    except Exception:
        return None, None


def _save_checkpoint(df: pd.DataFrame, meta: dict, sep: str):
    try:
        df.to_csv(str(CHECKPOINT_CSV), sep=sep, index=False)
        CHECKPOINT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[CHECKPOINT] Warning: could not save: {e}")


def _clear_checkpoint():
    for p in (CHECKPOINT_CSV, CHECKPOINT_META):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


def detect_sep(path: str) -> str:
    # Keep delimiter detection consistent with the rest of the project
    candidates = [",", ";", "\t"]
    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
            lines = []
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                if line.strip():
                    lines.append(line)
        if not lines:
            return ";"

        sample = "".join(lines)
        try:
            sniffed = (
                csv.Sniffer().sniff(sample, delimiters="".join(candidates)).delimiter
            )
            if sniffed in candidates:
                return sniffed
        except Exception:
            pass

        def score(delim: str) -> tuple[int, int, int]:
            counts = []
            bad = 0
            for ln in lines:
                try:
                    row = next(
                        csv.reader(
                            [ln], delimiter=delim, quotechar='"', escapechar="\\"
                        )
                    )
                    counts.append(len(row))
                except Exception:
                    bad += 1
            if not counts:
                return (0, -10_000, -1_000 - bad)
            mode = max(set(counts), key=counts.count)
            var = sum(abs(c - mode) for c in counts)
            return (mode, -var, -(bad))

        return max(candidates, key=score)
    except Exception:
        return ";"


def _read_input(path: str, sep: str = None) -> "pd.DataFrame":
    ext = Path(path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path, sep=sep or detect_sep(path), encoding="utf-8-sig")


def process_file_with_layers(
    input_path: str,
    output_path: str,
    columns_to_anonymize: list,
    layers: list,
    sep: str = None,
):
    is_xlsx = Path(input_path).suffix.lower() in (".xlsx", ".xls")
    if not is_xlsx and sep is None:
        sep = detect_sep(input_path)

    # Always read original texts from source for end-of-run verification.
    df_original = _read_input(input_path, sep)
    original_texts = {
        col: df_original[col].copy()
        for col in columns_to_anonymize
        if col in df_original.columns
    }

    # Check for a resumable checkpoint.
    checkpoint_df, checkpoint_meta = _load_checkpoint(input_path, sep)
    if checkpoint_df is not None:
        df = checkpoint_df
        completed_columns = set(checkpoint_meta.get("completed_columns", []))
        checkpoint_col = checkpoint_meta.get("current_col")
        checkpoint_batch_end = checkpoint_meta.get("current_batch_end", 0)
        yield (
            json.dumps({
                "status": "progress",
                "message": f"Resuming from checkpoint ({len(completed_columns)} column(s) already done)...",
                "progress": 5,
            }) + "\n"
        )
    else:
        df = df_original.copy()
        completed_columns = set()
        checkpoint_col = None
        checkpoint_batch_end = 0
        yield (
            json.dumps({"status": "progress", "message": "Initializing...", "progress": 5})
            + "\n"
        )

    stat = os.stat(input_path)
    meta = {
        "input_size": stat.st_size,
        "input_mtime": stat.st_mtime,
        "sep": sep,
        "selected_columns": columns_to_anonymize,
        "selected_layers": layers,
        "completed_columns": list(completed_columns),
    }

    # Save immediately so a resume banner appears even if the very first batch crashes.
    if checkpoint_df is None:
        _save_checkpoint(df, meta, sep)

    try:
        validate_selected_layers(layers)
    except Exception as e:
        yield (
            json.dumps(
                {
                    "status": "error",
                    "error": str(e),
                    "message": "Model preflight failed before anonymization started.",
                    "progress": 0,
                }
            )
            + "\n"
        )
        return

    # Layer config toggles (mirrors the other project’s intent)
    layer_config = {"names": True, "locations": True, "pii": True, "titles": True}

    if "presidio" in layers:
        yield (
            json.dumps(
                {
                    "status": "progress",
                    "message": "Loading Layer 1 (Presidio)...",
                    "progress": 10,
                }
            )
            + "\n"
        )
    if "eu-pii" in layers:
        yield (
            json.dumps(
                {
                    "status": "progress",
                    "message": "Loading Layer 2 (EU-PII-Safeguard)...",
                    "progress": 20,
                }
            )
            + "\n"
        )
    if "openai-privacy-filter" in layers:
        yield (
            json.dumps(
                {
                    "status": "progress",
                    "message": "Loading Layer 2 (OpenAI Privacy Filter)...",
                    "progress": 20,
                }
            )
            + "\n"
        )

    total_cols = len(columns_to_anonymize)
    total_rows = len(df)

    for col_idx, col in enumerate(columns_to_anonymize):
        if col not in df.columns:
            yield (
                json.dumps(
                    {
                        "status": "progress",
                        "message": f"Column ‘{col}’ not found.",
                        "progress": 20,
                    }
                )
                + "\n"
            )
            continue

        if col in completed_columns:
            yield (
                json.dumps(
                    {
                        "status": "progress",
                        "message": f"Skipping ‘{col}’ (already done in checkpoint).",
                        "progress": 20 + int(70 * ((col_idx + 1) / total_cols)),
                    }
                )
                + "\n"
            )
            continue

        yield (
            json.dumps(
                {
                    "status": "progress",
                    "message": f"Anonymizing column: {col}...",
                    "progress": 20 + int(70 * (col_idx / total_cols)),
                }
            )
            + "\n"
        )

        # How far we already got in this column (0 = fresh start).
        resume_batch_end = checkpoint_batch_end if col == checkpoint_col else 0

        col_series = df[col]
        batch_starts = list(range(0, total_rows, _ANON_BATCH))
        for batch_start in batch_starts:
            batch_end = min(batch_start + _ANON_BATCH, total_rows)

            if batch_end <= resume_batch_end:
                # Already saved in checkpoint — skip without reprocessing.
                continue

            chunk_texts = []
            chunk_indices = []
            for i in range(batch_start, batch_end):
                text = col_series.at[i]
                if pd.isna(text) or not isinstance(text, str) or not text.strip():
                    continue
                chunk_texts.append(text)
                chunk_indices.append(i)

            if chunk_texts:
                masked = process_chunk_sync(chunk_texts, layer_config, layers)
                for row_i, new_val in zip(chunk_indices, masked):
                    df.at[row_i, col] = new_val

            # Checkpoint after every batch.
            meta["current_col"] = col
            meta["current_batch_end"] = batch_end
            _save_checkpoint(df, meta, sep)

            last_i = batch_end
            base_progress = 20 + int(70 * (col_idx / total_cols))
            row_progress = int((70 / total_cols) * (last_i / total_rows))
            preview_row = last_i - 1 if last_i else 0
            pv = col_series.at[preview_row] if preview_row >= 0 else ""
            yield (
                json.dumps(
                    {
                        "status": "progress",
                        "column": col,
                        "row": last_i,
                        "total_rows": total_rows,
                        "checkpoint_saved": True,
                        "preview": (str(pv)[:60] + "...")
                        if isinstance(pv, str) and pv
                        else "",
                        "progress": base_progress + row_progress,
                        "message": f"Processing rows 1–{last_i}/{total_rows} in {col} (batch {_ANON_BATCH})",
                    }
                )
                + "\n"
            )

        # Column done — update completed list and remove in-progress markers.
        completed_columns.add(col)
        meta["completed_columns"] = list(completed_columns)
        meta.pop("current_col", None)
        meta.pop("current_batch_end", None)
        _save_checkpoint(df, meta, sep)

    # --- Count what was masked (tags inserted into output) ---
    _TAG_RE = re.compile(r'\[(NAME|PII|LOCATION|TITLE)\]')
    total_cells = 0
    affected_cells = 0
    total_entities = 0
    tag_counts = {"NAME": 0, "PII": 0, "LOCATION": 0, "TITLE": 0}

    for col in columns_to_anonymize:
        if col in df.columns:
            for val in df[col]:
                if pd.isna(val) or not isinstance(val, str) or not val.strip():
                    continue
                total_cells += 1
                matches = _TAG_RE.findall(val)
                if matches:
                    affected_cells += 1
                    total_entities += len(matches)
                    for tag in matches:
                        tag_counts[tag] += 1

    df.to_csv(output_path, sep=sep, index=False)

    # --- Verification: detect entities in ORIGINAL text, check if they survived in output ---
    yield (
        json.dumps({"status": "progress", "message": "Verifying output...", "progress": 98})
        + "\n"
    )

    from src.core.layers.layer1_presidio import collect_presidio_spans
    from src.core.layers.privacy_pipeline import _filter_spans, unload_all_layer_models

    layer_config = {"names": True, "locations": True, "pii": True, "titles": True}
    missed_counts = {"NAME": 0, "PII": 0, "LOCATION": 0, "TITLE": 0}
    missed_samples = {"NAME": [], "PII": [], "LOCATION": [], "TITLE": []}
    removed_samples = {"NAME": [], "PII": [], "LOCATION": [], "TITLE": []}

    for col in columns_to_anonymize:
        if col not in df.columns:
            continue
        for idx in range(len(df)):
            original_val = original_texts.get(col, pd.Series(dtype=str)).iloc[idx] if col in original_texts else None
            anonymized_val = df[col].iloc[idx]

            if pd.isna(original_val) or not isinstance(original_val, str) or not original_val.strip():
                continue

            # Detect on clean original text, then apply the same filters as the main pipeline
            raw_spans = collect_presidio_spans(original_val, layer_config)
            filtered_spans = _filter_spans(original_val, raw_spans, layer_config)
            for start, end, tag in filtered_spans:
                key = tag.strip("[]")
                if key not in missed_counts:
                    continue
                entity_text = original_val[start:end]
                if isinstance(anonymized_val, str) and entity_text.lower() in anonymized_val.lower():
                    missed_counts[key] += 1
                    if entity_text not in missed_samples[key]:
                        missed_samples[key].append(entity_text)
                else:
                    if entity_text not in removed_samples[key]:
                        removed_samples[key].append(entity_text)

    _write_report(
        input_path=input_path,
        output_path=output_path,
        columns=columns_to_anonymize,
        layers=layers,
        total_rows=total_rows,
        total_cells=total_cells,
        affected_cells=affected_cells,
        total_entities=total_entities,
        tag_counts=tag_counts,
        missed_counts=missed_counts,
        missed_samples=missed_samples,
        removed_samples=removed_samples,
    )
    unload_all_layer_models(layers)
    _clear_checkpoint()

    yield (
        json.dumps(
            {
                "status": "success",
                "message": "Anonymization complete",
                "rows_processed": total_rows,
                "columns_anonymized": columns_to_anonymize,
                "progress": 100,
                "stats": {
                    "total_cells": total_cells,
                    "affected_cells": affected_cells,
                    "total_entities": total_entities,
                    "tag_counts": tag_counts,
                    "missed_counts": missed_counts,
                    "missed_samples": missed_samples,
                    "removed_samples": removed_samples,
                },
            }
        )
        + "\n"
    )


if __name__ == "__main__":
    INPUT_FILE = "data.csv"
    OUTPUT_FILE = "data_clean.csv"
    TARGET_COLUMNS = ["feedback_text", "open_comments"]

    process_file_with_layers(
        INPUT_FILE, OUTPUT_FILE, TARGET_COLUMNS, ["presidio", "eu-pii"]
    )
