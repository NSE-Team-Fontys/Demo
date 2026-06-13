from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Shared span-plausibility helpers
# Used by both layer1_presidio and layer2_eu_pii to filter false positives
# without hardcoding specific words — purely structural / shape-based rules.
# ---------------------------------------------------------------------------

# Uppercase letter immediately after a lowercase → CamelCase product/brand name.
_CAMELCASE_RE = re.compile(r"(?<=[a-z])[A-Z]")


def is_plausible_name_span(span_text: str) -> bool:
    """
    Return False if the span cannot be a person name by shape alone.

      1. All-caps ≤ 5 chars → acronym (SEO, CRO, START, …)
      2. Single token > 12 chars → Dutch compound noun
         (Medewerkerstevredenheid, Leergemeenschap, …)
      3. CamelCase single token → product / brand name (FeedPulse, …)
      4. All-lowercase → never a name
      5. Mostly digits → number, not a name
    """
    s = span_text.strip()
    if not s:
        return False
    is_single = " " not in s

    if s.isupper() and len(s) <= 5:
        return False
    if is_single and len(s) > 12:
        return False
    if is_single and _CAMELCASE_RE.search(s):
        return False
    if s.islower():
        return False
    if sum(c.isdigit() for c in s) / max(len(s), 1) > 0.5:
        return False
    return True


def is_plausible_location_span(span_text: str) -> bool:
    """
    Return False if the span cannot be a geographic location by shape alone.
    Real location names are short-to-medium proper nouns.

      1. Single token > 15 chars → Dutch compound noun
      2. CamelCase single token → product / platform name (YouTube, Portflow, …)
      3. All-lowercase single token → common word (peer, google, research, …)
      4. All-uppercase ≤ 5 chars without digits → abbreviation (START, HBO, …)
      5. Single token ending in a digit → team / group identifier, not a place
    """
    s = span_text.strip()
    if not s:
        return False
    is_single = " " not in s

    if is_single and len(s) > 15:
        return False
    if is_single and _CAMELCASE_RE.search(s):
        return False
    if is_single and s.isalpha() and s.islower():
        return False
    if is_single and s.isupper() and len(s) <= 5 and not any(c.isdigit() for c in s):
        return False
    if is_single and s[-1].isdigit():
        return False
    return True


def is_plausible_pii_span(span_text: str) -> bool:
    """
    Return False for EU-PII [PII] catch-all spans that are clearly not
    identifiers by shape alone.

      1. CamelCase single token → product / software name (ChatGPT, NotebookLM, …)
      2. All-lowercase single alphabetic token → common word (hulp, anders, …)
      3. All-uppercase ≤ 4 chars without digits → short abbreviation (HBO, …)
    """
    s = span_text.strip()
    if not s:
        return False
    is_single = " " not in s

    if is_single and _CAMELCASE_RE.search(s):
        return False
    if is_single and s.isalpha() and s.islower():
        return False
    if is_single and s.isupper() and len(s) <= 4 and not any(c.isdigit() for c in s):
        return False
    return True


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    tag: str


# Matches Dutch tussenvoegsels followed by a capitalized surname.
# Longer patterns listed first so "van den" is tried before "van".
# Covers: van den, van der, van de, op den, van, de, den, der, ten, ter, 't
_TUSSENVOEGSEL_RE = re.compile(
    r"(?:\s+"
    r"(?:van\s+den\s+|van\s+der\s+|van\s+de\s+|op\s+den\s+|van\s+|de\s+|den\s+|der\s+|ten\s+|ter\s+|'t\s+)"
    r"[A-Z\u00C0-\u024F][A-Za-z\u00C0-\u024F]+"
    r")+"
)


def extend_name_spans_for_tussenvoegsels(text: str, spans: list) -> list:
    """Extend [NAME] spans to include following Dutch tussenvoegsels and surnames.

    spaCy NER and regex patterns often stop at the first name token.
    This ensures 'Methodius' expands to 'Methodius van den Bogaert'.
    """
    result = []
    for start, end, tag in spans:
        if tag == "[NAME]":
            m = _TUSSENVOEGSEL_RE.match(text, end)
            if m:
                end = m.end()
        result.append((start, end, tag))
    return result


def apply_spans(text: str, spans: list[Span]) -> str:
    """Apply (start,end,tag) spans to text. Longest-first; non-overlapping wins."""
    if not spans or not text:
        return text

    # longest first to avoid partial clobbering
    ordered = sorted(spans, key=lambda s: (s.end - s.start, s.start), reverse=True)

    selected: list[Span] = []
    for s in ordered:
        if s.start < 0 or s.end > len(text) or s.start >= s.end:
            continue
        if not any(s.start < o.end and s.end > o.start for o in selected):
            selected.append(s)

    # apply from right to left so indices remain stable
    selected.sort(key=lambda s: s.start, reverse=True)
    out = text
    for s in selected:
        out = out[: s.start] + s.tag + out[s.end :]
    return out

