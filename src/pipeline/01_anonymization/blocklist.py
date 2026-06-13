from __future__ import annotations

import json
import re

from src.config.paths import WORD_BLOCKLIST_PATH


def load_blocklist() -> list[str]:
    """Return the current custom word blocklist, or [] if none saved."""
    try:
        if WORD_BLOCKLIST_PATH.exists():
            data = json.loads(WORD_BLOCKLIST_PATH.read_text(encoding="utf-8"))
            return [w for w in data.get("words", []) if isinstance(w, str) and w.strip()]
    except Exception:
        pass
    return []


def save_blocklist(words: list[str]) -> None:
    """Persist the blocklist to disk, deduplicating and stripping whitespace."""
    seen: set[str] = set()
    clean: list[str] = []
    for w in words:
        w = w.strip()
        if w and w.lower() not in seen:
            seen.add(w.lower())
            clean.append(w)
    WORD_BLOCKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    WORD_BLOCKLIST_PATH.write_text(
        json.dumps({"words": clean}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def apply_blocklist(text: str, words: list[str]) -> str:
    """
    Replace every whole-word (case-insensitive) occurrence of each blocklist
    entry in *text* with [PII].

    Applied as a post-processing step after the NER pipeline — it never
    touches the models and has no impact on anonymization performance.
    Phrases (multi-word entries) are matched literally with word boundaries
    at each end.
    """
    if not isinstance(text, str) or not text.strip() or not words:
        return text
    result = text
    for word in words:
        word = word.strip()
        if not word:
            continue
        pattern = re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE)
        result = pattern.sub("[PII]", result)
    return result
