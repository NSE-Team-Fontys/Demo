from importlib import import_module

_builder = import_module("src.pipeline.02_embedding.vector_builder")

VECTOR_CHECKPOINT = _builder.VECTOR_CHECKPOINT
build_metadata = _builder.build_metadata
build_vector_db = _builder.build_vector_db
build_vector_db_stream = _builder.build_vector_db_stream
detect_sep = _builder.detect_sep
is_questionnaire_column = _builder.is_questionnaire_column


def __getattr__(name):
    return getattr(_builder, name)


__all__ = [
    "VECTOR_CHECKPOINT",
    "build_metadata",
    "build_vector_db",
    "build_vector_db_stream",
    "detect_sep",
    "is_questionnaire_column",
]
