import json
import re

from src.config.themes import THEME_LLM_DEFINITIONS

ENGLISH_OUTPUT_INSTRUCTION = (
    "Gemma 4 output rules: write generated analytical fields in English "
    "(summary, positive_comments, critical_comments, subthemes, and manifest "
    "descriptions). Write positive_comments and critical_comments as concise "
    "synthesized points, not as quotes. Keep only student_suggestions as exact "
    "verbatim student comments in their original language."
)

SUBTHEME_MANIFEST_INSTRUCTION = (
    "Subtheme task: extract 3 to 5 short, dashboard-friendly subthemes that are "
    "specific to the selected theme and supported by the responses. For every "
    "subtheme, also return a subtheme_manifest entry with the same name, a "
    "one-sentence description, and evidence_ids copied exactly from the response "
    "IDs shown in brackets, such as E0001. Use only IDs that directly support "
    "that subtheme. Do not invent, rename, or reformat evidence IDs."
)

GEMMA_JSON_RESPONSE_CONTRACT = (
    "Gemma 4 response contract: return one valid JSON object only. Do not wrap "
    "the answer in Markdown, code fences, XML tags, analysis text, or reasoning. "
    "Use exactly the schema keys shown below; do not add extra keys. If a field "
    "has no supported evidence, return an empty array for list fields or a "
    "short evidence-bounded summary string for summary."
)

DASHBOARD_JSON_SCHEMA = """{
  "summary": "...",
  "positive_comments": ["..."],
  "critical_comments": ["..."],
  "student_suggestions": ["..."],
  "subthemes": ["...", "..."],
  "subtheme_manifest": [
    {"name": "...", "description": "...", "evidence_ids": ["E0001", "E0002"]}
  ]
}"""


def default_prompt(theme_name: str) -> str:
    return f"""Gemma 4 task: act as a strict JSON-only analyst for an education survey dashboard.
Read the following student survey responses about '{theme_name}' and turn them into one dashboard insight.
Theme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}
Scope rules:
- Use only the supplied responses as evidence.
- Only analyze comments as evidence for this selected theme.
- Ignore irrelevant parts of multi-topic responses.
- Do not infer facts, demographics, causes, or details that are not present in the responses.
{ENGLISH_OUTPUT_INSTRUCTION}
These responses may be the complete theme evidence set or one small enough to fit in a single prompt.
Generation tasks:
1. Summarize the general consensus in exactly 2 concise English sentences.
2. Write up to 3 concise English summaries of the strongest positive points students make.
3. Write up to 3 concise English summaries of the strongest critical points students make.
4. Select up to 3 exact student suggestions where students propose a solution, improvement, or concrete next step instead of only complaining.
5. Extract 3 to 5 short subthemes or topics mentioned within the selected theme.
{SUBTHEME_MANIFEST_INSTRUCTION}
{GEMMA_JSON_RESPONSE_CONTRACT}
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Responses:
"""


def _append_evidence(prompt: str, evidence: list) -> str:
    normalized = [
        item
        if isinstance(item, dict)
        else {"document": str(item), "evidence_type": "definite"}
        for item in evidence
    ]
    def _line(item: dict) -> str:
        evidence_id = str(item.get("evidence_id") or "").strip()
        prefix = f"[{evidence_id}] " if evidence_id else ""
        return f"- {prefix}{item['document']}\n"

    definite = [
        item
        for item in normalized
        if item.get("evidence_type")
        in {"definite", "free_text_retrieval", "subtheme_candidate"}
    ]
    ambiguous = [item for item in normalized if item.get("evidence_type") == "ambiguous"]
    prompt += "\nDefinite evidence:\n"
    for item in definite:
        prompt += _line(item)
    if ambiguous:
        prompt += (
            "\nAmbiguous candidate evidence:\n"
            "These responses were close classification candidates for this theme. "
            "Ignore any candidate evidence that is not genuinely relevant. A genuinely "
            "multi-topic response may contribute to this summary.\n"
        )
        for item in ambiguous:
            prompt += _line(item)
    return prompt


def build_prompt(theme_name: str, docs: list) -> str:
    return _append_evidence(default_prompt(theme_name), docs)


def build_batch_summary_prompt(
    theme_name: str,
    docs: list,
    *,
    batch_number: int,
    total_batches: int,
) -> str:
    prompt = (
        f"You are analyzing batch {batch_number} of {total_batches} for the survey theme "
        f"'{theme_name}'.\n"
        f"Theme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}\n"
        "Only analyze comments as evidence for this theme. Ignore parts of answers that "
        "clearly belong to another theme.\n"
        f"{ENGLISH_OUTPUT_INSTRUCTION}\n"
        f"{GEMMA_JSON_RESPONSE_CONTRACT}\n"
    )
    prompt += """\nThis is an intermediate map step, not the final theme summary. Summarize only this batch without making whole-theme prevalence claims.
Preserve concrete student suggestions as verbatim comments. Write positive_comments and critical_comments as concise English summaries, not quotes.
For subthemes, include evidence IDs from this batch only.
Respond EXACTLY in this JSON format:
""" + DASHBOARD_JSON_SCHEMA + """

Responses:
"""
    return _append_evidence(prompt, docs)


def build_reduce_prompt(
    theme_name: str,
    batch_summaries: list[dict],
    *,
    source_document_count: int,
) -> str:
    summaries_json = json.dumps(batch_summaries, ensure_ascii=False, indent=2)
    return f"""You are an expert data analyst. Merge the batch-level survey insights for '{theme_name}' into one final dashboard insight.
Theme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}
The batch summaries together represent {source_document_count} source student responses.
Only make claims supported by repeated or strong evidence in the batch summaries. Do not invent quotes or details.
{ENGLISH_OUTPUT_INSTRUCTION}
Summarize the general consensus in 2 sentences.
Write up to 3 concise English summaries of the strongest positive points students make. Write up to 3 concise English summaries of the strongest critical points students make. Do not present these as verbatim quotes.
Select up to 3 exact student suggestions from the batch summaries. Use verbatim text only; return an empty array if no clear suggestions exist.
Deduplicate repeated points across batches. Prefer patterns that appear in multiple batches, but keep a strong minority concern if it is concrete and important.
Also extract 3 to 5 short sub-themes or topics mentioned across the batch summaries.
Merge subtheme_manifest entries from the batch summaries. Preserve evidence_ids from the batch summaries and deduplicate them.
{GEMMA_JSON_RESPONSE_CONTRACT}
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Batch summaries:
{summaries_json}
"""


def build_subtheme_prompt(
    parent_theme_name: str,
    subtheme_name: str,
    docs: list,
) -> str:
    prompt = f"""You are an expert data analyst. Read the following student survey responses assigned to the parent theme '{parent_theme_name}'.
Subtheme focus: {subtheme_name}
Parent theme scope: {THEME_LLM_DEFINITIONS.get(parent_theme_name, parent_theme_name)}
Only analyze comments as evidence for the subtheme focus. Ignore responses, or parts of responses, that do not support this subtheme.
{ENGLISH_OUTPUT_INSTRUCTION}
Summarize the subtheme consensus in 2 sentences.
Write up to 3 concise English summaries of the strongest positive points students make for this subtheme. Write up to 3 concise English summaries of the strongest critical points students make for this subtheme. Do not present these as verbatim quotes.
Select up to 3 exact student suggestions where students propose a solution, improvement, or concrete next step for this subtheme. Use verbatim text only; return an empty array if no clear suggestions exist.
Also extract 3 to 5 more specific sub-topics within this subtheme, or return an empty list if the evidence is too narrow.
{GEMMA_JSON_RESPONSE_CONTRACT}
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Responses:
"""
    return _append_evidence(prompt, docs)


def build_subtheme_batch_summary_prompt(
    parent_theme_name: str,
    subtheme_name: str,
    docs: list,
    *,
    batch_number: int,
    total_batches: int,
) -> str:
    prompt = f"""You are analyzing batch {batch_number} of {total_batches} for a subtheme drilldown.
Parent theme: {parent_theme_name}
Subtheme focus: {subtheme_name}
Parent theme scope: {THEME_LLM_DEFINITIONS.get(parent_theme_name, parent_theme_name)}
Only analyze comments as evidence for the subtheme focus. Ignore irrelevant parent-theme evidence.
{ENGLISH_OUTPUT_INSTRUCTION}
{GEMMA_JSON_RESPONSE_CONTRACT}
This is an intermediate map step, not the final subtheme summary. Summarize only this batch without making whole-subtheme prevalence claims.
Preserve concrete student suggestions as verbatim comments. Write positive_comments and critical_comments as concise English summaries, not quotes.
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Responses:
"""
    return _append_evidence(prompt, docs)


def build_subtheme_reduce_prompt(
    parent_theme_name: str,
    subtheme_name: str,
    batch_summaries: list[dict],
    *,
    source_document_count: int,
) -> str:
    summaries_json = json.dumps(batch_summaries, ensure_ascii=False, indent=2)
    return f"""You are an expert data analyst. Merge the batch-level survey insights for subtheme '{subtheme_name}' within parent theme '{parent_theme_name}'.
The batch summaries together represent {source_document_count} candidate source student responses.
Only make claims supported by repeated or strong evidence in the batch summaries. Do not invent quotes or details.
{ENGLISH_OUTPUT_INSTRUCTION}
Summarize the subtheme consensus in 2 sentences.
Write up to 3 concise English summaries of the strongest positive points students make. Write up to 3 concise English summaries of the strongest critical points students make. Do not present these as verbatim quotes.
Select up to 3 exact student suggestions from the batch summaries. Use verbatim text only; return an empty array if no clear suggestions exist.
Deduplicate repeated points across batches. Prefer patterns that appear in multiple batches, but keep a strong minority concern if it is concrete and important.
Also extract 3 to 5 more specific sub-topics within this subtheme, or return an empty list if the evidence is too narrow.
{GEMMA_JSON_RESPONSE_CONTRACT}
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Batch summaries:
{summaries_json}
"""


def _strip_thinking_block(text: str) -> str:
    """Remove Gemma-style <think>...</think> blocks before JSON extraction."""
    return re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()


def _remove_trailing_commas_before_closers(json_str: str) -> str:
    result: list[str] = []
    in_string = False
    escape_next = False

    for char in json_str:
        if escape_next:
            result.append(char)
            escape_next = False
            continue
        if char == "\\" and in_string:
            result.append(char)
            escape_next = True
            continue
        if char == '"':
            result.append(char)
            in_string = not in_string
            continue
        if not in_string and char in "}]":
            while result and result[-1].isspace():
                result.pop()
            if result and result[-1] == ",":
                result.pop()
        result.append(char)

    return "".join(result)


def _escape_control_chars_in_strings(json_str: str) -> str:
    result: list[str] = []
    in_string = False
    escape_next = False

    for char in json_str:
        if escape_next:
            result.append(char)
            escape_next = False
            continue
        if char == "\\" and in_string:
            result.append(char)
            escape_next = True
            continue
        if char == '"':
            result.append(char)
            in_string = not in_string
            continue
        if in_string and ord(char) < 0x20:
            if char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            else:
                result.append(f"\\u{ord(char):04x}")
            continue
        result.append(char)

    return "".join(result)


def _json_object_candidates(text: str) -> tuple[list[str], str]:
    candidates: list[str] = []
    stack: list[str] = []
    start: int | None = None
    in_string = False
    escape_next = False

    for index, char in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if char == "\\" and in_string:
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            if not stack:
                start = index
            stack.append("}")
        elif char == "[" and stack:
            stack.append("]")
        elif char in "}]" and stack and stack[-1] == char:
            stack.pop()
            if not stack and start is not None:
                candidates.append(text[start : index + 1])
                start = None

    partial = text[start:] if start is not None else ""
    return candidates, partial


def _drop_trailing_incomplete_object_member(json_str: str) -> str | None:
    stack: list[str] = []
    in_string = False
    escape_next = False
    last_top_level_comma: int | None = None

    for index, char in enumerate(json_str):
        if escape_next:
            escape_next = False
            continue
        if char == "\\" and in_string:
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in "}]" and stack and stack[-1] == char:
            stack.pop()
        elif char == "," and stack == ["}"]:
            last_top_level_comma = index

    if last_top_level_comma is None:
        return None
    return json_str[:last_top_level_comma]


def _repair_truncated_json(json_str: str) -> dict:
    """Close open brackets/strings in a truncated JSON and attempt to parse it."""
    stack: list[str] = []
    in_string = False
    escape_next = False

    for char in json_str:
        if escape_next:
            escape_next = False
            continue
        if char == "\\" and in_string:
            escape_next = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            stack.append("}")
        elif char == "[":
            stack.append("]")
        elif char in "}]" and stack and stack[-1] == char:
            stack.pop()

    repaired = json_str
    if in_string:
        repaired += '"'
    repaired += "".join(reversed(stack))
    repaired = _escape_control_chars_in_strings(repaired)
    repaired = _remove_trailing_commas_before_closers(repaired)
    return json.loads(repaired)


def _repair_json_object(json_str: str) -> dict:
    try:
        return _repair_truncated_json(json_str)
    except Exception:
        trimmed = _drop_trailing_incomplete_object_member(json_str)
        if trimmed:
            return _repair_truncated_json(trimmed)
        raise


def parse_llm_json(result_text: str) -> dict:
    cleaned = _strip_thinking_block(result_text)
    candidates, partial = _json_object_candidates(cleaned)
    if partial:
        try:
            result = _repair_json_object(partial)
            print(
                f"[LLM] Warning: model output was truncated; partial JSON recovered "
                f"(first 80 chars: {partial[:80]!r})"
            )
            return result
        except Exception:
            pass

    for candidate in reversed(candidates):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        try:
            result = _repair_json_object(candidate)
            print(
                f"[LLM] Warning: model output needed JSON repair "
                f"(first 80 chars: {candidate[:80]!r})"
            )
            return result
        except Exception:
            pass

    json_start = cleaned.find("{")
    json_str = cleaned[json_start:] if json_start >= 0 else cleaned
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    try:
        result = _repair_json_object(json_str)
        print(
            f"[LLM] Warning: model output was truncated; partial JSON recovered "
            f"(first 80 chars: {json_str[:80]!r})"
        )
        return result
    except Exception as exc:
        raise RuntimeError(
            f"Invalid JSON structure returned by model: {json_str[:150]}"
        ) from exc
