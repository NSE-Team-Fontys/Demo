import json
import os

import pandas as pd

from src.config.paths import ANON_CHECKPOINT_CSV, ANON_CHECKPOINT_META

CHECKPOINT_CSV = ANON_CHECKPOINT_CSV
CHECKPOINT_META = ANON_CHECKPOINT_META


def load_checkpoint(input_path: str, sep: str):
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


def save_checkpoint(df: pd.DataFrame, meta: dict, sep: str):
    try:
        df.to_csv(str(CHECKPOINT_CSV), sep=sep, index=False)
        CHECKPOINT_META.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as exc:
        print(f"[CHECKPOINT] Warning: could not save: {exc}")


def clear_checkpoint():
    for path in (CHECKPOINT_CSV, CHECKPOINT_META):
        try:
            if path.exists():
                path.unlink()
        except Exception:
            pass
