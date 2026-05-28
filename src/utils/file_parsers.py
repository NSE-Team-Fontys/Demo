import csv
import json
from pathlib import Path

import pandas as pd

from src.config.paths import UPLOAD_FILE, UPLOAD_INFO_FILE
from src.config.themes import METADATA_COLS


def get_upload_path() -> str | None:
    if UPLOAD_INFO_FILE.exists():
        try:
            info = json.loads(UPLOAD_INFO_FILE.read_text(encoding="utf-8"))
            path = info.get("path")
            if path and Path(path).exists():
                return path
        except Exception:
            pass
    if UPLOAD_FILE.exists():
        return str(UPLOAD_FILE)
    return None


def save_uploaded_file(file) -> tuple[Path, str]:
    ext = Path(file.filename or "upload.csv").suffix.lower()
    if ext not in (".csv", ".xlsx", ".xls"):
        ext = ".csv"

    save_path = UPLOAD_FILE.with_suffix(ext)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    file.save(save_path)
    UPLOAD_INFO_FILE.write_text(
        json.dumps({"path": str(save_path), "ext": ext}),
        encoding="utf-8",
    )
    return save_path, ext


def read_dataframe(path: str | Path, sep: str = None, nrows: int = None) -> pd.DataFrame:
    ext = Path(path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        kwargs = {}
        if nrows is not None:
            kwargs["nrows"] = nrows
        return pd.read_excel(path, **kwargs)

    kwargs = {"encoding": "utf-8-sig"}
    if sep:
        kwargs["sep"] = sep
    if nrows is not None:
        kwargs["nrows"] = nrows
    return pd.read_csv(path, **kwargs)


def detect_sep(path: str | Path) -> str:
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
            sniffed = csv.Sniffer().sniff(sample, delimiters="".join(candidates)).delimiter
            if sniffed in candidates:
                return sniffed
        except Exception:
            pass

        def score(delim: str) -> tuple[int, int, int]:
            counts = []
            bad = 0
            for line in lines:
                try:
                    row = next(csv.reader([line], delimiter=delim, quotechar='"', escapechar="\\"))
                    counts.append(len(row))
                except Exception:
                    bad += 1
            if not counts:
                return (0, -10_000, -1_000 - bad)
            mode = max(set(counts), key=counts.count)
            variance = sum(abs(count - mode) for count in counts)
            return (mode, -variance, -bad)

        return max(candidates, key=score)
    except Exception:
        return ";"


def is_questionnaire_column(col: str) -> bool:
    name = str(col).strip()
    lower = name.lower()
    if name in METADATA_COLS or lower.startswith("themascore"):
        return False
    return (
        "?" in name
        or lower.startswith("wil jij")
        or lower.startswith("waarom")
        or lower.startswith("wat voor soort")
    )


def preview_records(df: pd.DataFrame) -> list[dict]:
    records = df.head(1).to_dict(orient="records")
    for record in records:
        for key, value in list(record.items()):
            if pd.isna(value):
                record[key] = None
    return records
