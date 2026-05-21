"""
Late-masking pipeline aligned with privacy_officer `privacy_agent`: collect spans from
layer 1 + layer 2, merge, filter, extend for quotes/possessives, apply once.

Avoids regex-replacing substrings on already-masked text (which corrupts output).
"""

from __future__ import annotations

import re
from typing import Optional, Set

from .layer1_presidio import collect_presidio_spans
from .layer_utils import extend_name_spans_for_tussenvoegsels

_NEVER_MASK_WORDS: Set[str] = {"meneer", "mevrouw"}
_HONORIFIC_WORDS: Set[str] = {
    "mevr.",
    "mevr",
    "dhr.",
    "dhr",
    "heer",
}

# Align with layer2_text_norm (ASCII apostrophe + Unicode right single quotation mark).
_POSSESSIVE_RE = re.compile(r"['\u2019][sS]\b")
_NAME_TOKEN_RE = re.compile(
    r"^[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F]+"
    r"(?:\s+(?:de|den|der|van|von|of|[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F]+))*$"
)
_NAME_CARRY_STOPWORDS: Set[str] = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "could",
    "for",
    "from",
    "het",
    "how",
    "our",
    "the",
    "this",
    "too",
    "van",
    "wat",
    "we",
    "which",
    "with",
    "would",
    "you",
}
_NAME_SPAN_STOPWORDS: Set[str] = _NAME_CARRY_STOPWORDS | {
    "course",
    "feedback",
    "module",
    "timely",
}


def extend_spans_for_original(text: str, spans: list) -> list:
    """
    Extend spans to include stripped possessive / surrounding quotes after NER normalization.
    """
    result = []
    for start, end, tag in spans:
        new_start, new_end = start, end
        if _POSSESSIVE_RE.match(text, new_end):
            new_end += 2
        if new_start > 0 and text[new_start - 1] == '"':
            new_start -= 1
        if new_end < len(text) and text[new_end] == '"':
            new_end += 1
        result.append((new_start, new_end, tag))
    return result


def _filter_spans(text: str, spans: list, config: Optional[dict]) -> list:
    titles_on = not config or config.get("titles", True)
    result = []
    for s, e, tag in spans:
        span_text = text[s:e]
        word_lower = span_text.strip().rstrip(".").lower()

        if word_lower in _NEVER_MASK_WORDS:
            continue
        if not titles_on and word_lower in _HONORIFIC_WORDS:
            continue
        if tag == "[NAME]" and not _is_plausible_name_span(span_text):
            continue

        new_s = s
        for hw in _NEVER_MASK_WORDS:
            prefix = hw + " "
            if span_text[: len(prefix)].lower() == prefix:
                new_s = s + len(prefix)
                break

        if new_s < e:
            result.append((new_s, e, tag))
    return result


def _is_plausible_name_span(span_text: str) -> bool:
    name = _canonical_name_for_carryforward(span_text)
    if len(name) < 3:
        return False
    if name.lower() in _NAME_SPAN_STOPWORDS:
        return False
    return bool(_NAME_TOKEN_RE.match(name))


def apply_all_masks(text: str, spans: list) -> str:
    if not spans:
        return text

    sorted_spans = sorted(spans, key=lambda x: x[1] - x[0], reverse=True)
    selected = []
    for start, end, tag in sorted_spans:
        if not any(start < se and end > ss for ss, se, _ in selected):
            selected.append((start, end, tag))

    selected.sort(key=lambda s: s[0], reverse=True)
    result = text
    for start, end, tag in selected:
        result = result[:start] + tag + result[end:]
    return result


def _build_carryforward_spans(texts: list, all_raw_spans: list) -> list:
    known_names: Set[str] = set()
    for text, spans in zip(texts, all_raw_spans):
        for start, end, tag in spans:
            if tag == "[NAME]":
                name = _canonical_name_for_carryforward(text[start:end])
                if _should_carryforward_name(name):
                    known_names.add(name)

    if not known_names:
        return [[] for _ in texts]

    extra_spans = []
    for text, spans in zip(texts, all_raw_spans):
        covered = [(s, e) for s, e, _ in spans]
        new_spans = []
        for name in known_names:
            pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
            for m in pattern.finditer(text):
                if not any(s <= m.start() < e or s < m.end() <= e for s, e in covered):
                    new_spans.append((m.start(), m.end(), "[NAME]"))
                    covered.append((m.start(), m.end()))
        extra_spans.append(new_spans)
    return extra_spans


def _canonical_name_for_carryforward(name: str) -> str:
    name = name.strip().strip('"')
    if _POSSESSIVE_RE.search(name):
        name = _POSSESSIVE_RE.sub("", name)
    for prefix in ("Docent ", "docent ", "Teacher ", "teacher ", "Professor ", "professor ", "Mentor ", "mentor "):
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    return name.strip()


def _should_carryforward_name(name: str) -> bool:
    if len(name) < 3:
        return False
    if name.lower() in _NAME_CARRY_STOPWORDS:
        return False
    if not _NAME_TOKEN_RE.match(name):
        return False
    return True


def collect_layer2_spans_batch(texts: list, config: Optional[dict], layers: list[str]) -> list:
    merged = [[] for _ in texts]
    if "eu-pii" in layers:
        from .layer2_eu_pii import eu_pii_collect_batch

        for i, sp in enumerate(eu_pii_collect_batch(texts, config)):
            merged[i].extend(sp)
    if "openai-privacy-filter" in layers:
        from .layer2_openai_privacy_filter import openai_privacy_filter_collect_batch

        for i, sp in enumerate(openai_privacy_filter_collect_batch(texts, config)):
            merged[i].extend(sp)
    return merged


def validate_selected_layers(layers: list[str]) -> None:
    """Fail fast when a selected layer is unavailable instead of silently skipping it."""
    if "presidio" in layers:
        from .layer1_presidio import ensure_presidio_available

        ensure_presidio_available()
    if "eu-pii" in layers:
        from .layer2_eu_pii import ensure_eu_pii_available

        ensure_eu_pii_available()
    if "openai-privacy-filter" in layers:
        from .layer2_openai_privacy_filter import ensure_openai_privacy_filter_available

        ensure_openai_privacy_filter_available()


def process_chunk_sync(batch: list[str], config: Optional[dict], layers: list[str]) -> list[str]:
    """
    Anonymize a batch of strings using the same span-merge rules as privacy_officer.
    """
    if not batch:
        return []

    use_l1 = "presidio" in layers
    use_l2 = "eu-pii" in layers or "openai-privacy-filter" in layers

    if use_l1:
        layer1_spans = [collect_presidio_spans(t, config) for t in batch]
    else:
        layer1_spans = [[] for _ in batch]

    if use_l2:
        layer2_spans = collect_layer2_spans_batch(batch, config, layers)
    else:
        layer2_spans = [[] for _ in batch]

    if not use_l1 and not use_l2:
        return list(batch)

    combined = [a + b for a, b in zip(layer1_spans, layer2_spans)]
    combined = [extend_name_spans_for_tussenvoegsels(t, s) for t, s in zip(batch, combined)]
    combined = [_filter_spans(t, s, config) for t, s in zip(batch, combined)]
    carryforward = _build_carryforward_spans(batch, combined)

    return [
        apply_all_masks(text, extend_spans_for_original(text, spans + extra))
        for text, spans, extra in zip(batch, combined, carryforward)
    ]
