import json
from datetime import datetime

from src.config.paths import ANON_REPORT_FILE, ANON_REPORT_JSON

REPORT_FILE = ANON_REPORT_FILE
REPORT_JSON = ANON_REPORT_JSON


def write_report(
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
    if total_cells:
        lines.append(
            f"Cells affected  : {affected_cells}  "
            f"({100 * affected_cells / total_cells:.1f}%)"
        )
    else:
        lines.append(f"Cells affected  : {affected_cells}")
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
            for sample in missed_samples.get(tag, []):
                lines.append(f"    - {sample}")
    if not any_missed:
        lines.append("  (none)")

    lines.append("")
    lines.append("Entities successfully removed:")
    for tag, samples in removed_samples.items():
        if samples:
            lines.append(f"  [{tag}]  {len(samples)} unique:")
            for sample in samples:
                lines.append(f"    - {sample}")
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
        REPORT_JSON.write_text(
            json.dumps(stats_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[REPORT] Saved to {REPORT_FILE} and {REPORT_JSON}")
    except Exception as exc:
        print(f"[REPORT] Warning: could not save report: {exc}")
