import json
import re

from src.config.themes import THEME_LLM_DEFINITIONS

ENGLISH_OUTPUT_INSTRUCTION = (
    "Write generated fields in English: summary, positive_comments, "
    "critical_comments, and subthemes. Keep only student_suggestions as exact "
    "verbatim student comments in their original language."
)

SUBTHEME_MANIFEST_INSTRUCTION = (
    "For every subtheme, also return subtheme_manifest entries with the same "
    "name, a one-sentence description, and evidence_ids copied exactly from the "
    "response IDs shown in brackets, such as E0001. Use only IDs that directly "
    "support that subtheme."
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
    return f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Theme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}
Only analyze comments as evidence for this theme. Do not drift into Support / Mentoring unless the selected theme is Support / Mentoring.
{ENGLISH_OUTPUT_INSTRUCTION}
These responses may be the complete theme evidence set or one small enough to fit in a single prompt.
Summarize the general consensus in 2 sentences.
Write up to 3 concise English summaries of the strongest positive points students make. Write up to 3 concise English summaries of the strongest critical points students make. Do not present these as verbatim quotes.
Select up to 3 exact student suggestions where students propose a solution, improvement, or concrete next step instead of only complaining. Use verbatim text only; return an empty array if no clear suggestions exist.
Also extract 3 to 5 short sub-themes or topics mentioned.
{SUBTHEME_MANIFEST_INSTRUCTION}
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


def build_prompt(theme_name: str, docs: list, custom_prompt: str = "") -> str:
    if custom_prompt.strip():
        prompt = (
            custom_prompt.replace("{theme_name}", theme_name)
            + f"\n\nTheme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}"
            + f"\n{ENGLISH_OUTPUT_INSTRUCTION}"
            + f"\n{SUBTHEME_MANIFEST_INSTRUCTION}"
            + f"\nRespond EXACTLY in this JSON format:\n{DASHBOARD_JSON_SCHEMA}"
            + "\n\nResponses:\n"
        )
    else:
        prompt = default_prompt(theme_name)

    return _append_evidence(prompt, docs)


def build_batch_summary_prompt(
    theme_name: str,
    docs: list,
    *,
    batch_number: int,
    total_batches: int,
    custom_prompt: str = "",
) -> str:
    prompt = (
        f"You are analyzing batch {batch_number} of {total_batches} for the survey theme "
        f"'{theme_name}'.\n"
        f"Theme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}\n"
        "Only analyze comments as evidence for this theme. Ignore parts of answers that "
        "clearly belong to another theme.\n"
        f"{ENGLISH_OUTPUT_INSTRUCTION}\n"
    )
    if custom_prompt.strip():
        prompt += f"\nAdditional analyst instruction:\n{custom_prompt.replace('{theme_name}', theme_name)}\n"
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
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Batch summaries:
{summaries_json}
"""


def build_subtheme_prompt(
    parent_theme_name: str,
    subtheme_name: str,
    docs: list,
    custom_prompt: str = "",
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
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Responses:
"""
    if custom_prompt.strip():
        prompt += f"\nAdditional analyst instruction:\n{custom_prompt.replace('{theme_name}', parent_theme_name)}\n"
    return _append_evidence(prompt, docs)


def build_subtheme_batch_summary_prompt(
    parent_theme_name: str,
    subtheme_name: str,
    docs: list,
    *,
    batch_number: int,
    total_batches: int,
    custom_prompt: str = "",
) -> str:
    prompt = f"""You are analyzing batch {batch_number} of {total_batches} for a subtheme drilldown.
Parent theme: {parent_theme_name}
Subtheme focus: {subtheme_name}
Parent theme scope: {THEME_LLM_DEFINITIONS.get(parent_theme_name, parent_theme_name)}
Only analyze comments as evidence for the subtheme focus. Ignore irrelevant parent-theme evidence.
{ENGLISH_OUTPUT_INSTRUCTION}
This is an intermediate map step, not the final subtheme summary. Summarize only this batch without making whole-subtheme prevalence claims.
Preserve concrete student suggestions as verbatim comments. Write positive_comments and critical_comments as concise English summaries, not quotes.
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Responses:
"""
    if custom_prompt.strip():
        prompt += f"\nAdditional analyst instruction:\n{custom_prompt.replace('{theme_name}', parent_theme_name)}\n"
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
Respond EXACTLY in this JSON format:
{DASHBOARD_JSON_SCHEMA}

Batch summaries:
{summaries_json}
"""


def parse_llm_json(result_text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", result_text)
    json_str = match.group(0) if match else result_text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON structure returned by model: {json_str[:150]}"
        ) from exc
