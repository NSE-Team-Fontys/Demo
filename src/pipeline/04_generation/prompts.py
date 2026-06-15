import json
import re

from src.config.themes import THEME_LLM_DEFINITIONS

ENGLISH_OUTPUT_INSTRUCTION = (
    "Write generated fields in English: summary, sentiment points, positive_comments, "
    "critical_comments, and subthemes. Keep only student_suggestions as exact "
    "verbatim student comments in their original language."
)


def default_prompt(theme_name: str) -> str:
    return f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Theme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}
Only analyze comments as evidence for this theme. Do not drift into Support / Mentoring unless the selected theme is Support / Mentoring.
{ENGLISH_OUTPUT_INSTRUCTION}
These responses may be the complete theme evidence set or one small enough to fit in a single prompt.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Write up to 3 concise English summaries of the strongest positive points students make. Write up to 3 concise English summaries of the strongest critical points students make. Do not present these as verbatim quotes.
Select up to 3 exact student suggestions where students propose a solution, improvement, or concrete next step instead of only complaining. Use verbatim text only; return an empty array if no clear suggestions exist.
Also extract 3 to 5 short sub-themes or topics mentioned.
Respond EXACTLY in this JSON format:
{{
  "summary": "...",
  "sentiments": [
    {{"sentiment": "Positive", "point": "..."}}
  ],
  "positive_comments": ["..."],
  "critical_comments": ["..."],
  "student_suggestions": ["..."],
  "subthemes": ["...", "..."]
}}

Responses:
"""


def _append_evidence(prompt: str, evidence: list) -> str:
    normalized = [
        item
        if isinstance(item, dict)
        else {"document": str(item), "evidence_type": "definite"}
        for item in evidence
    ]
    definite = [
        item["document"]
        for item in normalized
        if item.get("evidence_type") in {"definite", "free_text_retrieval"}
    ]
    ambiguous = [
        item["document"]
        for item in normalized
        if item.get("evidence_type") == "ambiguous"
    ]
    prompt += "\nDefinite evidence:\n"
    for document in definite:
        prompt += f"- {document}\n"
    if ambiguous:
        prompt += (
            "\nAmbiguous candidate evidence:\n"
            "These responses were close classification candidates for this theme. "
            "Ignore any candidate evidence that is not genuinely relevant. A genuinely "
            "multi-topic response may contribute to this summary.\n"
        )
        for document in ambiguous:
            prompt += f"- {document}\n"
    return prompt


def build_prompt(theme_name: str, docs: list, custom_prompt: str = "") -> str:
    if custom_prompt.strip():
        prompt = (
            custom_prompt.replace("{theme_name}", theme_name)
            + f"\n\nTheme scope: {THEME_LLM_DEFINITIONS.get(theme_name, theme_name)}"
            + f"\n{ENGLISH_OUTPUT_INSTRUCTION}"
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
Respond EXACTLY in this JSON format:
{
  "summary": "...",
  "sentiments": [
    {"sentiment": "Positive", "point": "..."}
  ],
  "positive_comments": ["..."],
  "critical_comments": ["..."],
  "student_suggestions": ["..."],
  "subthemes": ["...", "..."]
}

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
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Write up to 3 concise English summaries of the strongest positive points students make. Write up to 3 concise English summaries of the strongest critical points students make. Do not present these as verbatim quotes.
Select up to 3 exact student suggestions from the batch summaries. Use verbatim text only; return an empty array if no clear suggestions exist.
Deduplicate repeated points across batches. Prefer patterns that appear in multiple batches, but keep a strong minority concern if it is concrete and important.
Also extract 3 to 5 short sub-themes or topics mentioned across the batch summaries.
Respond EXACTLY in this JSON format:
{{
  "summary": "...",
  "sentiments": [
    {{"sentiment": "Positive", "point": "..."}}
  ],
  "positive_comments": ["..."],
  "critical_comments": ["..."],
  "student_suggestions": ["..."],
  "subthemes": ["...", "..."]
}}

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
