from __future__ import annotations

import re
from dataclasses import dataclass


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

