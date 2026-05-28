from importlib import import_module
import json
from pathlib import Path

from src.config.paths import ANONYMIZED_CSV_PATH, SEP_FILE
from src.utils.file_parsers import (
    detect_sep,
    get_upload_path,
    is_questionnaire_column,
    preview_records,
    read_dataframe,
    save_uploaded_file,
)

_engine = import_module("src.pipeline.01_anonymization.engine")


def inspect_uploaded_file(file) -> dict:
    if not file:
        raise ValueError("No file uploaded")

    save_path, ext = save_uploaded_file(file)
    sep = None
    if ext == ".csv":
        sep = detect_sep(save_path)
        SEP_FILE.parent.mkdir(parents=True, exist_ok=True)
        SEP_FILE.write_text(sep, encoding="utf-8")

    df = read_dataframe(save_path, sep=sep, nrows=5)
    return {
        "status": "success",
        "columns": df.columns.tolist(),
        "preview": preview_records(df),
    }


def anonymize_uploaded_file(selected_columns: list, selected_layers: list):
    upload_path = get_upload_path()
    if not upload_path:
        raise FileNotFoundError("No file uploaded")

    input_file = Path(upload_path)
    if input_file.suffix.lower() == ".csv":
        sep = SEP_FILE.read_text(encoding="utf-8").strip() if SEP_FILE.exists() else detect_sep(input_file)
    else:
        sep = ","

    print(
        f"[ANONYMIZE] Columns: {selected_columns} | "
        f"Layers: {selected_layers} | sep={repr(sep)}"
    )
    return _engine.process_file_with_layers(
        str(input_file),
        str(ANONYMIZED_CSV_PATH),
        selected_columns,
        selected_layers,
        sep=sep,
    )


def inspect_anonymized_file() -> dict:
    if not ANONYMIZED_CSV_PATH.exists():
        raise FileNotFoundError("Anonymized CSV not found")

    sep = detect_sep(ANONYMIZED_CSV_PATH)
    df = read_dataframe(ANONYMIZED_CSV_PATH, sep=sep, nrows=0)
    all_columns = df.columns.tolist()
    text_columns = [col for col in all_columns if is_questionnaire_column(col)]

    with open(ANONYMIZED_CSV_PATH, encoding="utf-8") as f:
        row_count = sum(1 for _ in f) - 1

    return {
        "status": "success",
        "columns": all_columns,
        "text_columns": text_columns,
        "row_count": row_count,
    }


def run_anonymize_check_stream():
    original_path = get_upload_path()
    if not original_path or not Path(original_path).exists():
        raise FileNotFoundError(
            "Origineel bestand niet gevonden. Upload het bestand opnieuw."
        )
    if not ANONYMIZED_CSV_PATH.exists():
        raise FileNotFoundError(
            "Geanonimiseerd bestand niet gevonden. Voer eerst de anonimisering uit."
        )

    columns = None
    if _engine.REPORT_JSON.exists():
        try:
            columns = json.loads(
                _engine.REPORT_JSON.read_text(encoding="utf-8")
            ).get("columns")
        except Exception:
            pass
    if not columns:
        sep = detect_sep(ANONYMIZED_CSV_PATH)
        df_tmp = read_dataframe(ANONYMIZED_CSV_PATH, sep=sep, nrows=0)
        columns = [col for col in df_tmp.columns if is_questionnaire_column(col)]

    return _engine.run_check_stream(original_path, str(ANONYMIZED_CSV_PATH), columns)


def anonymize_report_payload() -> dict:
    if not _engine.REPORT_JSON.exists():
        return {"has_report": False}
    try:
        data = json.loads(_engine.REPORT_JSON.read_text(encoding="utf-8"))
        return {"has_report": True, **data}
    except Exception as exc:
        return {"has_report": False, "error": str(exc)}


def checkpoint_status_payload() -> dict:
    if not _engine.CHECKPOINT_META.exists():
        return {"has_checkpoint": False}
    try:
        meta = json.loads(_engine.CHECKPOINT_META.read_text(encoding="utf-8"))
        return {
            "has_checkpoint": True,
            "completed_columns": meta.get("completed_columns", []),
            "total_columns": meta.get("selected_columns", []),
            "selected_layers": meta.get("selected_layers", []),
            "current_col": meta.get("current_col"),
        }
    except Exception:
        return {"has_checkpoint": False}
