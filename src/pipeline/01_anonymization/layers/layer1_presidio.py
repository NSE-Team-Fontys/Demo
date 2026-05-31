from __future__ import annotations

import logging
import os
import subprocess
import sys
from typing import Optional

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from src.utils.model_device import describe_model_device, get_model_device

from .layer2_text_norm import normalize_for_ner
from .layer_utils import extend_name_spans_for_tussenvoegsels

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------------
# Pattern + operator logic copied from privacy_officer (simplified: no spaCy NL model bootstrap here).
# -----------------------------------------------------------------------------

PRESIDIO_PATTERN_DEFINITIONS = [
    {
        "entity": "STUDENT_NUMBER",
        "patterns": [Pattern(name="student_number", regex=r"\b[0-9]{5,7}\b", score=0.85)],
        "context": None,
    },
    {
        "entity": "USERNAME",
        "patterns": [
            Pattern(name="at_handle", regex=r"@[\w]+", score=0.9),
            Pattern(name="underscore_username", regex=r"\b[\w]+(?:_[\w]+)+\b", score=0.75),
            Pattern(
                name="username_with_digits",
                regex=r"\b[a-zA-Z][a-zA-Z0-9_]{1,25}\d{2,}[a-zA-Z0-9_]*\b",
                score=0.75,
            ),
        ],
        "context": ["insta", "instagram", "github", "account", "handle", "username", "profiel", "genaamd", "bekend"],
    },
    {
        "entity": "OBFUSCATED_EMAIL",
        "patterns": [
            Pattern(
                name="dutch_spelled_email",
                regex=r"[\w_]+(?:\s+(?:punt|\.)\s+[\w_]+)+\s+apenstaartje\s+[\w_]+(?:\s+(?:punt|\.)\s+[\w_]+)+",
                score=0.85,
            ),
        ],
        "context": ["mail", "mailen", "email", "bereiken", "contact"],
    },
    {
        "entity": "BUILDING_OR_ROOM",
        "patterns": [
            Pattern(name="room_code", regex=r"\b(?:R|TQ|TL|TX)\s*\d+(?:[.,]\d+)?\b", score=0.8),
            Pattern(name="lokaal_number", regex=r"\b(?:lokaal|gebouw|ruimte)\s+\d+(?:[.,]\d+)?\b", score=0.85),
        ],
        "context": ["lokaal", "gebouw", "lokaalnummer", "kamer", "ruimte"],
    },
    {
        "entity": "FLOOR_REFERENCE",
        "patterns": [
            Pattern(name="floor_numeric", regex=r"\b\d+[e]\s+etage\b", score=0.9),
            Pattern(
                name="floor_written",
                regex=r"\b(?:eerste|tweede|derde|vierde|vijfde|zesde|zevende|achtste|negende|tiende)\s+etage\b",
                score=0.9,
            ),
        ],
        "context": ["etage", "verdieping", "gebouw"],
    },
    {
        "entity": "TEACHER_NAME_CONTEXT",
        "patterns": [
            Pattern(
                name="possessive_name_before_academic_term",
                regex=r"\b[A-Z][a-z]+(?:['’]s)?\b(?=\s+(?:grading|grades|feedback|assessment|assessments|marking|module|course|corrects))",
                score=0.9,
            ),
            Pattern(
                name="name_after_teacher_context",
                regex=r"(?:(?<=[Dd]ocent )|(?<=[Tt]eacher )|(?<=[Pp]rofessor )|(?<=[Mm]entor ))[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F]+(?:\s+[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F]+)*(?:[‘’]s)?",
                score=0.9,
            ),
        ],
        "context": ["grading", "grades", "feedback", "assessment", "docent", "teacher", "professor", "mentor"],
    },
    {
        "entity": "NL_BSN",
        "patterns": [
            Pattern(name="nl_bsn_dots", regex=r"\b\d{3}\.\d{2}\.\d{3}\b", score=0.95),
            Pattern(name="nl_bsn_plain", regex=r"\b\d{9}\b", score=0.75),
        ],
        "context": ["bsn", "burgerservicenummer", "sofinummer", "identificatie"],
    },
    {
        "entity": "DUTCH_POSTCODE",
        "patterns": [Pattern(name="dutch_postcode", regex=r"\b\d{4}\s?[A-Z]{2}\b", score=0.9)],
        "context": ["postcode", "adres", "straat", "woonplaats", "zip"],
    },
    {
        "entity": "DUTCH_PHONE",
        "patterns": [
            Pattern(name="dutch_mobile", regex=r"\b06[-\s]\d{2}[-\s]?\d{2}[-\s]?\d{2}[-\s]?\d{2}\b", score=0.9),
            Pattern(name="dutch_mobile_intl", regex=r"\b\+316\d{8}\b", score=0.95),
        ],
        "context": None,
    },
    {
        "entity": "DUTCH_HONORIFIC",
        "patterns": [
            Pattern(
                name="dutch_honorific",
                regex=r"\b(?:Mevrouw|mevrouw|Meneer|meneer|Mevr\.|mevr\.|Dhr\.|dhr\.|heer|Heer)\b",
                score=0.9,
            ),
        ],
        "context": None,
    },
]

PRESIDIO_OPERATORS = {
    "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
    "NRP": OperatorConfig("replace", {"new_value": "[NAME]"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[PII]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PII]"}),
    "STUDENT_NUMBER": OperatorConfig("replace", {"new_value": "[PII]"}),
    "USERNAME": OperatorConfig("replace", {"new_value": "[PII]"}),
    "OBFUSCATED_EMAIL": OperatorConfig("replace", {"new_value": "[PII]"}),
    "BUILDING_OR_ROOM": OperatorConfig("keep"),
    "FLOOR_REFERENCE": OperatorConfig("keep"),
    "TEACHER_NAME_CONTEXT": OperatorConfig("replace", {"new_value": "[NAME]"}),
    "NL_BSN": OperatorConfig("replace", {"new_value": "[PII]"}),
    "DUTCH_POSTCODE": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
    "DUTCH_PHONE": OperatorConfig("replace", {"new_value": "[PII]"}),
    "DUTCH_HONORIFIC": OperatorConfig("replace", {"new_value": "[TITLE]"}),
    "DEFAULT": OperatorConfig("keep"),
}

_analyzer: AnalyzerEngine | None = None
_anonymizer = AnonymizerEngine()


def unload_models() -> None:
    global _analyzer
    _analyzer = None
    import gc
    gc.collect()


_SPACY_NL_MODEL = "nl_core_news_lg"
_SPACY_EN_MODEL = "en_core_web_lg"
_SPACY_NL_WHL = "https://github.com/explosion/spacy-models/releases/download/nl_core_news_lg-3.8.0/nl_core_news_lg-3.8.0-py3-none-any.whl"
_SPACY_EN_WHL = "https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl"


def _spacy_model_installed(name: str) -> bool:
    try:
        import spacy.util

        return bool(spacy.util.is_package(name))
    except Exception:
        return False


def _ensure_spacy_models() -> None:
    """
    Ensure the required spaCy NL/EN models are installed.
    By default, auto-installs via pip if missing.

    Set env var DISABLE_SPACY_MODEL_AUTO_INSTALL=1 to disable auto-install.
    """
    if os.environ.get("DISABLE_SPACY_MODEL_AUTO_INSTALL", "").lower() in {"1", "true", "yes"}:
        return

    missing = []
    if not _spacy_model_installed(_SPACY_NL_MODEL):
        missing.append((_SPACY_NL_MODEL, _SPACY_NL_WHL))
    if not _spacy_model_installed(_SPACY_EN_MODEL):
        missing.append((_SPACY_EN_MODEL, _SPACY_EN_WHL))

    if not missing:
        return

    logger.info("spaCy model(s) missing: %s. Installing now...", ", ".join(m for m, _ in missing))
    for model_name, whl_url in missing:
        # Install the wheel URL directly (matches requirements.txt pins).
        subprocess.check_call([sys.executable, "-m", "pip", "install", whl_url])
        logger.info("Installed spaCy model: %s", model_name)


def _init_spacy_device() -> str:
    """
    Activate the same device that get_model_device() picked for the rest
    of the pipeline. Must be called BEFORE any spaCy model is loaded.
    Returns the device that was actually activated.
    """
    import spacy

    device = get_model_device()

    if device == "cuda":
        try:
            from thinc.api import use_pytorch_for_gpu_memory
            use_pytorch_for_gpu_memory()
        except Exception as e:
            logger.warning("use_pytorch_for_gpu_memory failed: %s", e)
        activated = spacy.prefer_gpu()
        if not activated:
            logger.warning(
                "spaCy could not activate CUDA — falling back to CPU. "
                "Check that cupy-cuda12x is installed in this interpreter "
                "(`python -c \"import cupy; print(cupy.__version__)\"`) and "
                "that the CUDA major version matches your driver."
            )
            return "cpu"
        logger.info("Presidio spaCy running on %s", describe_model_device("cuda"))
        return "cuda"

    if device == "mps":
        try:
            import thinc_apple_ops  # noqa: F401
            logger.info("Presidio spaCy running with thinc-apple-ops (Apple Accelerate).")
        except ImportError:
            logger.info(
                "Presidio spaCy running on CPU (Mac). "
                "Install 'thinc-apple-ops' for an Apple-Silicon speedup."
            )
        return "mps"

    spacy.require_cpu()
    logger.info("Presidio spaCy running on CPU.")
    return "cpu"


def _build_analyzer() -> AnalyzerEngine:
    """
    Build an AnalyzerEngine with spaCy NL+EN models.
    This demo is configured to ALWAYS use the spaCy NLP engine for best NER quality.
    """
    _ensure_spacy_models()
    _init_spacy_device()
    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "nl", "model_name": _SPACY_NL_MODEL},
                {"lang_code": "en", "model_name": _SPACY_EN_MODEL},
            ],
        }
    )
    nlp_engine = provider.create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["nl", "en"])
    register_custom_presidio_recognizers(analyzer)
    logger.info("Presidio spaCy engines loaded (nl_core_news_lg + en_core_web_lg).")
    return analyzer


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = _build_analyzer()
    return _analyzer


def register_custom_presidio_recognizers(analyzer_engine: AnalyzerEngine) -> None:
    for defn in PRESIDIO_PATTERN_DEFINITIONS:
        entity = defn["entity"]
        patterns = defn["patterns"]
        context = defn.get("context")
        for lang in ("nl", "en"):
            rec = PatternRecognizer(
                supported_entity=entity,
                patterns=patterns,
                supported_language=lang,
                context=context,
            )
            analyzer_engine.registry.add_recognizer(rec)


def build_presidio_operators(config: Optional[dict] = None) -> dict:
    if not config:
        return dict(PRESIDIO_OPERATORS)

    ops = {"DEFAULT": OperatorConfig("keep")}
    # match privacy_officer intent: allow toggles
    if config.get("names", True):
        ops["PERSON"] = OperatorConfig("replace", {"new_value": "[NAME]"})
        ops["NRP"] = OperatorConfig("replace", {"new_value": "[NAME]"})
        ops["TEACHER_NAME_CONTEXT"] = OperatorConfig("replace", {"new_value": "[NAME]"})
    else:
        ops["PERSON"] = OperatorConfig("keep")
        ops["NRP"] = OperatorConfig("keep")
        ops["TEACHER_NAME_CONTEXT"] = OperatorConfig("keep")
    if config.get("locations", True):
        ops["LOCATION"] = OperatorConfig("replace", {"new_value": "[LOCATION]"})
        ops["DUTCH_POSTCODE"] = OperatorConfig("replace", {"new_value": "[LOCATION]"})
    else:
        ops["LOCATION"] = OperatorConfig("keep")
        ops["DUTCH_POSTCODE"] = OperatorConfig("keep")
    # Buildings and floors are always kept — Fontys wants to see which building is mentioned.
    ops["BUILDING_OR_ROOM"] = OperatorConfig("keep")
    ops["FLOOR_REFERENCE"] = OperatorConfig("keep")
    if config.get("titles", True):
        ops["DUTCH_HONORIFIC"] = OperatorConfig("replace", {"new_value": "[TITLE]"})
    else:
        ops["DUTCH_HONORIFIC"] = OperatorConfig("keep")
    if config.get("pii", True):
        for e in (
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "STUDENT_NUMBER",
            "USERNAME",
            "OBFUSCATED_EMAIL",
            "NL_BSN",
            "DUTCH_PHONE",
        ):
            ops[e] = OperatorConfig("replace", {"new_value": "[PII]"})
    else:
        for e in (
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "STUDENT_NUMBER",
            "USERNAME",
            "OBFUSCATED_EMAIL",
            "NL_BSN",
            "DUTCH_PHONE",
        ):
            ops[e] = OperatorConfig("keep")
    return ops


def ensure_presidio_available() -> None:
    """Raise if Presidio/spaCy cannot be initialized for the selected layer."""
    try:
        _get_analyzer()
    except Exception as e:
        raise RuntimeError(
            "Presidio is selected but its spaCy NLP engine could not be loaded. "
            "Check the nl_core_news_lg/en_core_web_lg installation or allow the model auto-install."
        ) from e


def collect_presidio_spans(text: str, config: Optional[dict] = None) -> list[tuple[int, int, str]]:
    """
    Run Presidio analysis on length-preserving normalized text and return (start, end, tag).
    Matches privacy_officer late-masking mode (offsets align with original text).
    """
    if not isinstance(text, str) or not text.strip():
        return []
    analyzer = _get_analyzer()
    try:
        try:
            lang = detect(text)
            if lang not in ("nl", "en"):
                lang = "nl"
        except LangDetectException:
            lang = "nl"

        results = analyzer.analyze(text=normalize_for_ner(text), language=lang)
        ops = build_presidio_operators(config)
        spans = []
        for result in results:
            op = ops.get(result.entity_type) or ops.get("DEFAULT")
            if op and op.operator_name == "replace":
                tag = op.params.get("new_value", "[PII]")
                spans.append((result.start, result.end, tag))
        return extend_name_spans_for_tussenvoegsels(text, spans)
    except Exception as e:
        logger.error("Presidio collect error on %r…: %s", str(text)[:30], e)
        return []


def anonymize_with_presidio(text: str, config: Optional[dict] = None) -> str:
    """Layer 1 masking (no span plumbing): returns text with tags."""
    if not isinstance(text, str) or not text.strip():
        return text
    analyzer = _get_analyzer()
    try:
        lang = detect(text)
        if lang not in ("nl", "en"):
            lang = "nl"
    except LangDetectException:
        lang = "nl"

    results = analyzer.analyze(text=text, language=lang)
    ops = build_presidio_operators(config)
    return _anonymizer.anonymize(text=text, analyzer_results=results, operators=ops).text


def presidio_masking_spec() -> dict:
    """For UI: what Presidio layer masks into which tags."""
    return {
        "[NAME]": ["PERSON", "NRP", "TEACHER_NAME_CONTEXT"],
        "[LOCATION]": ["LOCATION", "DUTCH_POSTCODE", "FLOOR_REFERENCE"],
        "[PII]": [
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "STUDENT_NUMBER",
            "USERNAME",
            "OBFUSCATED_EMAIL",
            "NL_BSN",
            "DUTCH_PHONE",
        ],
        "[TITLE]": ["DUTCH_HONORIFIC"],
    }

