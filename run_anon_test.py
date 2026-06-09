#!/usr/bin/env python3
"""
Standalone anonymization quality check.

Runs the anonymization pipeline on a real CSV/Excel file (or built-in
synthetic data) and saves a machine-readable report for before/after
comparison.

Output files:
  data/anonymization_report.json   — stats + missed/removed samples
  data/anonymization_report.txt    — human-readable version
  data/anon_test_output.csv        — anonymized output (real-file mode)

Usage:
    # With your own file — list columns first:
    python run_anon_test.py --input path/to/file.csv --list-columns

    # Then run on the columns that contain open text:
    python run_anon_test.py --input path/to/file.csv --columns "col1,col2"

    # Skip the HF model (no download, no HEALTH tags):
    python run_anon_test.py --input path/to/file.csv --columns "col1" --presidio-only

    # Skip verification (much faster on big files):
    python run_anon_test.py --input path/to/file.csv --columns "col1" --no-verify

    # Use built-in synthetic data (no --input needed):
    python run_anon_test.py
"""
from __future__ import annotations

import argparse
import csv
import importlib
import json
import sys
from datetime import datetime
from pathlib import Path

# ── project root ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import os
os.chdir(ROOT)

import src.config.runtime  # loads .env (ANONYMIZE_BATCH_SIZE, OMP_NUM_THREADS, etc.) before any other import
from src.config.paths import ANON_CHECKPOINT_CSV, ANON_CHECKPOINT_META, ANON_REPORT_JSON, DATA_DIR

# ── built-in synthetic data (used when no --input is given) ───────────────────
SURVEY_ROWS = [
    "Docent Jan van der Berg geeft heldere uitleg en is altijd bereikbaar.",
    "De begeleider mevrouw Jansen is erg vriendelijk en behulpzaam.",
    "Meneer Pietersen legt moeilijke stof goed uit, duidelijke docent.",
    "De coach was Sandra de Groot, zij begeleidde ons de hele minor.",
    "J. de Vries staat bekend om zijn strenge maar eerlijke beoordelingen.",
    "A.B.C. van den Hoeven is onze studiecoach en heel toegankelijk.",
    "Mijn studentnummer is 1234567 en ik heb moeite met inschrijven.",
    "Student 9876543 heeft een klacht ingediend bij de decaan.",
    "Er deden 45678 mensen mee aan dit onderzoek.",
    "Module 2 telde 3 toetsen en 12345 punten in totaal.",
    "Stuur vragen naar p.jansen@fontys.nl, zij helpt je verder.",
    "Bereikbaar via pietersen apenstaartje student punt fontys punt nl.",
    "Bel mij op 06-12 34 56 78 voor een afspraak na het college.",
    "+31 6 87654321 is het directe nummer van de studieadviseur.",
    "Het spreekuur is in lokaal R1.023 op de Eindhoven campus.",
    "Kantoor: Rachelsmolen 1, 5612 MA Eindhoven. Kom gerust langs.",
    "Stuur de vergoeding naar rekeningnummer NL91 ABNA 0417 1643 00.",
    "Mijn IBAN is NL29INGB0001234567 voor de terugbetaling.",
    "Ik heb ADHD en dat maakt het plannen van opdrachten lastiger voor mij.",
    "Door mijn depressie lukt het soms niet om alle colleges bij te wonen.",
    "Het vak statistiek was uitdagend maar leerzaam en goed gestructureerd.",
    "De cursus duurde 20 weken met drie toetsmomenten en een eindopdracht.",
    "Er zijn dit jaar 2024 aanmeldingen ontvangen voor de opleiding.",
]


# ── helpers ────────────────────────────────────────────────────────────────────

def _clear_stale_checkpoint() -> None:
    for p in (ANON_CHECKPOINT_CSV, ANON_CHECKPOINT_META):
        if p.exists():
            p.unlink()


def _write_synthetic_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "feedback_tekst"])
        for i, row in enumerate(SURVEY_ROWS, 1):
            writer.writerow([i, row])


def _load_dataframe(file_path: str):
    from src.utils.file_parsers import detect_sep, read_dataframe
    path = Path(file_path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return read_dataframe(file_path)
    return read_dataframe(file_path, sep=detect_sep(file_path))


def _auto_detect_columns(file_path: str) -> list[str]:
    """Return questionnaire columns detected by the built-in NSE heuristic."""
    from src.utils.file_parsers import is_questionnaire_column
    df = _load_dataframe(file_path)
    return [col for col in df.columns if is_questionnaire_column(col)]


def _list_columns(file_path: str) -> None:
    """Print column names and a sample value from the file, then exit."""
    from src.utils.file_parsers import is_questionnaire_column

    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    df = _load_dataframe(file_path)

    print(f"\nFile   : {file_path}")
    print(f"Rows   : {len(df)}")
    print(f"Columns ({len(df.columns)}):\n")

    for col in df.columns:
        auto = " ← auto-detected" if is_questionnaire_column(col) else ""
        sample = ""
        for val in df[col]:
            if isinstance(val, str) and val.strip():
                sample = val.strip()[:80]
                break
        print(f"  {col!r}{auto}")
        if sample:
            print(f"    sample: {sample!r}")

    print()
    print("Columns marked '← auto-detected' will be anonymized automatically.")
    print("Override with --columns \"col1,col2,...\" if needed.")
    print()
    sys.exit(0)


def _run_pipeline(input_path: str, output_path: str, layers: list, columns: list, verify: bool):
    from src.utils.file_parsers import detect_sep
    from pathlib import Path as _Path

    engine = importlib.import_module("src.pipeline.01_anonymization.engine")

    sep = None
    if _Path(input_path).suffix.lower() not in (".xlsx", ".xls"):
        sep = detect_sep(input_path)

    gen = engine.process_file_with_layers(
        input_path=input_path,
        output_path=output_path,
        columns_to_anonymize=columns,
        layers=layers,
        sep=sep,
        run_verification=verify,
    )

    stats = None
    for line in gen:
        try:
            event = json.loads(line.strip())
        except json.JSONDecodeError:
            continue
        status = event.get("status")
        if status == "progress":
            pct = event.get("progress", 0)
            msg = event.get("message", "")
            print(f"  [{pct:3d}%] {msg}")
        elif status == "success":
            stats = event.get("stats", {})
            print("  [100%] Done.\n")
        elif status == "error":
            print(f"\n  [ERROR] {event.get('error', 'unknown error')}")
            sys.exit(1)
    return stats


def _print_results(stats: dict) -> None:
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Cells scanned   : {stats.get('total_cells', 0)}")
    print(f"Cells affected  : {stats.get('affected_cells', 0)}")
    print(f"Entities masked : {stats.get('total_entities', 0)}")
    print()
    print("Tag breakdown:")
    for tag, count in stats.get("tag_counts", {}).items():
        bar = "#" * min(count, 40)
        print(f"  [{tag:<8}] {count:5d}  {bar}")

    missed = stats.get("missed_samples", {})
    any_missed = any(v for v in missed.values())
    print()
    if any_missed:
        print("MISSED — still present in output (verification):")
        for tag, samples in missed.items():
            if samples:
                print(f"  [{tag}]: {', '.join(repr(s) for s in samples[:8])}")
    else:
        print("Missed: none detected by verification.")


def _print_row_comparison(input_csv: str, output_csv: str, columns: list) -> None:
    import pandas as pd
    from src.utils.file_parsers import detect_sep, read_dataframe
    from pathlib import Path as _Path

    if _Path(input_csv).suffix.lower() in (".xlsx", ".xls"):
        df_in = read_dataframe(input_csv)
    else:
        df_in = read_dataframe(input_csv, sep=detect_sep(input_csv))

    df_out = pd.read_csv(output_csv)

    # For large files show only the first 30 changed rows
    MAX_ROWS = 30
    print()
    print("=" * 60)
    print("PER-ROW COMPARISON (first changed rows shown)")
    print("=" * 60)

    changed = 0
    for idx, row_idx in enumerate(df_in.index):
        for col in columns:
            if col not in df_in.columns or col not in df_out.columns:
                continue
            orig = str(df_in.at[row_idx, col])
            anon = str(df_out.iloc[idx][col]) if idx < len(df_out) else ""
            if orig != anon:
                changed += 1
                if changed <= MAX_ROWS:
                    print(f"\nRow {row_idx + 1} [{col}]:")
                    print(f"  IN : {orig[:120]}")
                    print(f"  OUT: {anon[:120]}")

    if changed > MAX_ROWS:
        print(f"\n  ... {changed - MAX_ROWS} more changed rows not shown ...")

    unchanged = len(df_in) - changed
    print(f"\nTotal rows   : {len(df_in)}")
    print(f"Rows changed : {changed}")
    print(f"Rows unchanged: {unchanged}")


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Anonymization quality check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", metavar="FILE",
                        help="Path to your CSV or Excel file")
    parser.add_argument("--columns", metavar="COL1,COL2",
                        help="Comma-separated column names to anonymize")
    parser.add_argument("--list-columns", action="store_true",
                        help="Print column names from --input and exit")
    parser.add_argument("--presidio-only", action="store_true",
                        help="Layer 1 only (Presidio/spaCy) — no HF download needed")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip verification step (much faster on large files)")
    parser.add_argument("--verify-only", action="store_true",
                        help="Only run verification on existing input + anon_test_output.csv (no re-anonymization)")
    parser.add_argument("--verify-sample", metavar="N", type=int, default=None,
                        help="Check only N random rows per column during verification (default: all rows)")
    args = parser.parse_args()

    # ── --verify-only mode ───────────────────────────────────────────────────
    if args.verify_only:
        if not args.input:
            print("--verify-only requires --input (the original file)")
            sys.exit(1)
        input_path = args.input
        output_path = str(DATA_DIR / "anon_test_output.csv")
        if not Path(output_path).exists():
            print(f"No anonymized output found at {output_path}")
            print("Run without --verify-only first to produce the anonymized file.")
            sys.exit(1)
        if args.columns:
            columns = [c.strip() for c in args.columns.split(",") if c.strip()]
        else:
            columns = _auto_detect_columns(input_path)
        from src.utils.file_parsers import detect_sep
        sep = detect_sep(input_path) if Path(input_path).suffix.lower() not in (".xlsx", ".xls") else None
        print()
        print("=" * 60)
        print(f"Verification-only — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Original : {input_path}")
        print(f"Anonymized: {output_path}")
        print(f"Report   : {ANON_REPORT_JSON}")
        print("=" * 60)
        print()
        engine = importlib.import_module("src.pipeline.01_anonymization.engine")
        for line in engine.run_check_stream(input_path, output_path, columns, sep=sep, sample_rows=args.verify_sample):
            try:
                event = json.loads(line.strip())
            except json.JSONDecodeError:
                continue
            status = event.get("status")
            if status == "progress":
                print(f"  [{event.get('progress', 0):3d}%] {event.get('message', '')}")
            elif status == "success":
                print("  [100%] Done.\n")
                _print_results(event.get("stats", {}))
            elif status == "error":
                print(f"\n  [ERROR] {event.get('error', 'unknown error')}")
                sys.exit(1)
        print()
        print(f"Report saved to: {ANON_REPORT_JSON}")
        sys.exit(0)

    # ── --list-columns mode ──────────────────────────────────────────────────
    if args.list_columns:
        if not args.input:
            print("--list-columns requires --input")
            sys.exit(1)
        _list_columns(args.input)

    # ── resolve input / output paths and columns ─────────────────────────────
    if args.input:
        input_path = args.input
        if not Path(input_path).exists():
            print(f"File not found: {input_path}")
            sys.exit(1)
        if args.columns:
            columns = [c.strip() for c in args.columns.split(",") if c.strip()]
        else:
            columns = _auto_detect_columns(input_path)
            if not columns:
                print("No questionnaire columns auto-detected.")
                print("Run with --list-columns to see all columns, then pass --columns.")
                sys.exit(1)
            print(f"Auto-detected columns: {', '.join(repr(c) for c in columns)}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(DATA_DIR / "anon_test_output.csv")
    else:
        # Synthetic data mode
        input_path = str(DATA_DIR / "anon_test_input.csv")
        output_path = str(DATA_DIR / "anon_test_output.csv")
        columns = ["feedback_tekst"]
        _write_synthetic_csv(Path(input_path))

    layers = ["presidio"] if args.presidio_only else ["presidio", "eu-pii"]

    # ── header ───────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"Anonymization Quality Check — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print(f"Input   : {input_path}")
    print(f"Output  : {output_path}")
    print(f"Report  : {ANON_REPORT_JSON}")
    print(f"Columns : {', '.join(columns)}")
    print(f"Layers  : {', '.join(layers)}")
    if not args.presidio_only:
        print("  (EU-PII model downloads ~500 MB on first run if not cached)")
    if args.no_verify:
        print("  (verification skipped — no missed-sample report)")
    print("=" * 60)
    print()

    stats = _run_pipeline(input_path, output_path, layers, columns, verify=not args.no_verify)
    if stats is None:
        print("Pipeline returned no stats.")
        sys.exit(1)

    _print_results(stats)

    # Row comparison: skip for very large files unless explicitly requested
    # (reading two full DataFrames into memory for a huge file is expensive)
    from src.utils.file_parsers import detect_sep, read_dataframe
    try:
        if Path(input_path).suffix.lower() in (".xlsx", ".xls"):
            row_count = len(read_dataframe(input_path))
        else:
            row_count = len(read_dataframe(input_path, sep=detect_sep(input_path)))
    except Exception:
        row_count = 0

    if row_count <= 5000:
        _print_row_comparison(input_path, output_path, columns)
    else:
        print(f"\n(Row comparison skipped for large file — {row_count} rows)")
        print("Check data/anon_test_output.csv directly.")

    print()
    print("=" * 60)
    print(f"Full JSON report: {ANON_REPORT_JSON}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
