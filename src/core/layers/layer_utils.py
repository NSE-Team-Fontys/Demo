from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    tag: str


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

