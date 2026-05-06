import csv
import json
import os

import pandas as pd

from src.core.layers.privacy_pipeline import process_chunk_sync, validate_selected_layers

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Chunk size for span collection + masking (Layer 2 HF batching).
# Default 512 for betere throughput; override via ANONYMIZE_BATCH_SIZE indien nodig.
_ANON_BATCH = int(os.environ.get("ANONYMIZE_BATCH_SIZE", "512"))


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


def process_file_with_layers(
    input_path: str,
    output_path: str,
    columns_to_anonymize: list,
    layers: list,
    sep: str = None,
):
    if sep is None:
        sep = detect_sep(input_path)
    df = pd.read_csv(input_path, sep=sep, encoding="utf-8-sig")

    yield (
        json.dumps({"status": "progress", "message": "Initializing...", "progress": 5})
        + "\n"
    )

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
        if col in df.columns:
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

            col_series = df[col]
            batch_starts = list(range(0, total_rows, _ANON_BATCH))
            for batch_start in batch_starts:
                batch_end = min(batch_start + _ANON_BATCH, total_rows)
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
                            "preview": (str(pv)[:60] + "...")
                            if isinstance(pv, str) and pv
                            else "",
                            "progress": base_progress + row_progress,
                            "message": f"Processing rows 1–{last_i}/{total_rows} in {col} (batch {_ANON_BATCH})",
                        }
                    )
                    + "\n"
                )
        else:
            yield (
                json.dumps(
                    {
                        "status": "progress",
                        "message": f"Column '{col}' not found.",
                        "progress": 20,
                    }
                )
                + "\n"
            )

    df.to_csv(output_path, sep=sep, index=False)
    yield (
        json.dumps(
            {
                "status": "success",
                "message": "Anonymization complete",
                "rows_processed": total_rows,
                "columns_anonymized": columns_to_anonymize,
                "progress": 100,
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
