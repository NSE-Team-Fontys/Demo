"""
PII False Positive Checker
--------------------------
Reads the original (non-anonymized) file, runs Presidio span detection on each
free-text unit, then asks llama3.1:8b (via Ollama) whether each detected entity
is a TRUE_POSITIVE or FALSE_POSITIVE.

Supported file types:
  - .txt  : each non-empty line is treated as one text unit (no --columns needed)
  - .csv  : requires --columns
  - .xlsx : requires --columns

Usage:
    # TXT file
    python pii_false_positive_checker.py \
        --input  data/anonymization_report.txt \
        --limit 5 s
        --output results/fp_report.json

    # CSV/XLSX file
    python pii_false_positive_checker.py \
        --input  data/your_original_file.csv \
        --columns feedback_text open_comments \
        --limit 50 \
        --output results/fp_report.json

Requirements:
    pip install ollama pandas openpyxl
    ollama pull llama3.1:8b   (done automatically if not yet pulled)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd
import ollama

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "llama3.1:8b"

SYSTEM_PROMPT = """\
You are a strict PII validation assistant. Your only job is to review detected \
PII entities and judge whether each one is real personal data or a false positive.

Definitions:
- TRUE_POSITIVE  : the value genuinely identifies or could help identify a real person \
(name, phone, email, BSN, address, IBAN, date of birth, etc.)
- FALSE_POSITIVE : a common noun, job title, company name, product name, place used \
as a general reference, or any value that is clearly not personally identifying in context

Rules:
- Use the surrounding text to decide — context is everything
- Text may be in Dutch or English
- Return ONLY valid JSON — no markdown fences, no explanation outside the JSON
- Never skip an entity from the input list

Output schema (one object per input entity, same order):
{
  "results": [
    {
      "entity": "<exact value from text>",
      "type": "<PII_TYPE>",
      "verdict": "TRUE_POSITIVE" | "FALSE_POSITIVE",
      "reason": "<one short sentence in English>"
    }
  ]
}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_input(path: str, sep: str | None = None) -> pd.DataFrame | list[str]:
    p = Path(path)
    if p.suffix.lower() == ".txt":
        lines = p.read_text(encoding="utf-8").splitlines()
        return [l for l in lines if l.strip()]
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    sep = sep or ","
    return pd.read_csv(p, sep=sep, encoding="utf-8", on_bad_lines="skip")


def _detect_spans(text: str) -> list[dict]:
    """Run Presidio + filter and return entity dicts."""
    from src.core.layers.layer1_presidio import collect_presidio_spans
    from src.core.layers.privacy_pipeline import _filter_spans

    layer_config = {"names": True, "locations": True, "pii": True, "titles": True}
    raw = collect_presidio_spans(text, layer_config)
    filtered = _filter_spans(text, raw, layer_config)
    return [
        {"entity": text[s:e], "type": tag.strip("[]")}
        for s, e, tag in filtered
    ]


def _ask_llm(text: str, entities: list[dict]) -> list[dict]:
    """Send text + entities to llama3.1:8b and parse the JSON response."""
    user_msg = (
        f'Text:\n"""\n{text}\n"""\n\n'
        f"Detected entities:\n{json.dumps(entities, ensure_ascii=False, indent=2)}\n\n"
        "Validate each entity."
    )
    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        options={"temperature": 0},
    )
    raw = response["message"]["content"].strip()
    # Strip accidental markdown fences
    if raw.startswith("```"):
        raw = "\n".join(
            line for line in raw.splitlines()
            if not line.strip().startswith("```")
        )
    return json.loads(raw)["results"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(
    input_path: str,
    columns: list[str],
    output_path: str,
    sep: str | None = None,
    limit: int | None = None,
) -> None:
    print(f"[INFO] Model  : {MODEL}")
    print(f"[INFO] Input  : {input_path}")
    print(f"[INFO] Columns: {columns}")
    print(f"[INFO] Limit  : {limit or 'all rows'}")
    print()

    data = _read_input(input_path, sep)
    is_txt = isinstance(data, list)

    if is_txt:
        lines = data[:limit] if limit else data
        total = len(lines)
    else:
        valid_cols = [c for c in (columns or []) if c in data.columns]
        if not valid_cols:
            sys.exit(f"[ERROR] None of {columns} found in {input_path}. Available: {list(data.columns)}")
        lines = None
        rows = data.head(limit) if limit else data
        total = len(rows)

    report: list[dict] = []
    fp_total = 0
    tp_total = 0
    error_total = 0

    if is_txt:
        for idx, cell in enumerate(lines):
            entities = _detect_spans(cell)
            if not entities:
                continue

            print(f"  line {idx + 1}/{total} | {len(entities)} entities detected", end=" ... ", flush=True)
            t0 = time.time()

            try:
                results = _ask_llm(cell, entities)
            except (json.JSONDecodeError, KeyError) as exc:
                print(f"PARSE ERROR ({exc})")
                error_total += 1
                report.append({"line": idx, "text_snippet": cell[:120], "entities": entities, "error": str(exc)})
                continue

            elapsed = time.time() - t0
            fps = [r for r in results if r.get("verdict") == "FALSE_POSITIVE"]
            tps = [r for r in results if r.get("verdict") == "TRUE_POSITIVE"]
            fp_total += len(fps)
            tp_total += len(tps)
            print(f"TP={len(tps)} FP={len(fps)} ({elapsed:.1f}s)")
            report.append({"line": idx, "text_snippet": cell[:120], "entities_detected": len(entities), "results": results})
    else:
        for row_idx, (_, row) in enumerate(rows.iterrows()):
            for col in valid_cols:
                cell = row.get(col)
                if not isinstance(cell, str) or not cell.strip():
                    continue

                entities = _detect_spans(cell)
                if not entities:
                    continue

                print(f"  row {row_idx + 1}/{total} | col '{col}' | {len(entities)} entities detected", end=" ... ", flush=True)
                t0 = time.time()

                try:
                    results = _ask_llm(cell, entities)
                except (json.JSONDecodeError, KeyError) as exc:
                    print(f"PARSE ERROR ({exc})")
                    error_total += 1
                    report.append({"row": row_idx, "column": col, "text_snippet": cell[:120], "entities": entities, "error": str(exc)})
                    continue

                elapsed = time.time() - t0
                fps = [r for r in results if r.get("verdict") == "FALSE_POSITIVE"]
                tps = [r for r in results if r.get("verdict") == "TRUE_POSITIVE"]
                fp_total += len(fps)
                tp_total += len(tps)
                print(f"TP={len(tps)} FP={len(fps)} ({elapsed:.1f}s)")
                report.append({"row": row_idx, "column": col, "text_snippet": cell[:120], "entities_detected": len(entities), "results": results})

    # Summary
    checked = tp_total + fp_total
    fp_rate = round(fp_total / checked * 100, 1) if checked else 0.0
    summary = {
        "model": MODEL,
        "input_file": input_path,
        "columns": valid_cols,
        "rows_sampled": total,
        "cells_with_entities": len(report),
        "true_positives": tp_total,
        "false_positives": fp_total,
        "false_positive_rate_pct": fp_rate,
        "parse_errors": error_total,
    }

    print()
    print("=" * 50)
    print(f"  True positives  : {tp_total}")
    print(f"  False positives : {fp_total}")
    print(f"  FP rate         : {fp_rate}%")
    print(f"  Parse errors    : {error_total}")
    print("=" * 50)

    output = {"summary": summary, "details": report}
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[INFO] Report saved to {output_path}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check PII false positives with llama3.1:8b")
    parser.add_argument("--input",   required=True, help="Path to original (non-anonymized) CSV or XLSX file")
    parser.add_argument("--columns", required=False, nargs="+", help="Column name(s) containing free text (not needed for .txt files)")
    parser.add_argument("--output",  default="results/fp_report.json", help="Output JSON report path")
    parser.add_argument("--sep",     default=None,  help="CSV separator (auto-detected if omitted)")
    parser.add_argument("--limit",   type=int, default=None, help="Max number of rows to process (default: all)")
    args = parser.parse_args()

    run(
        input_path=args.input,
        columns=args.columns,
        output_path=args.output,
        sep=args.sep,
        limit=args.limit,
    )
