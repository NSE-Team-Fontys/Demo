from importlib import import_module

_engine = import_module("src.pipeline.01_anonymization.engine")

CHECKPOINT_CSV = _engine.CHECKPOINT_CSV
CHECKPOINT_META = _engine.CHECKPOINT_META
REPORT_FILE = _engine.REPORT_FILE
REPORT_JSON = _engine.REPORT_JSON
detect_sep = _engine.detect_sep
process_file_with_layers = _engine.process_file_with_layers
run_check_stream = _engine.run_check_stream


def __getattr__(name):
    return getattr(_engine, name)


__all__ = [
    "CHECKPOINT_CSV",
    "CHECKPOINT_META",
    "REPORT_FILE",
    "REPORT_JSON",
    "detect_sep",
    "process_file_with_layers",
    "run_check_stream",
]
