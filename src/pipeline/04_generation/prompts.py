import json
import re

from src.config.themes import THEME_DEFINITIONS


def default_prompt(theme_name: str) -> str:
    return f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Theme scope: {THEME_DEFINITIONS.get(theme_name, theme_name)}
Only analyze comments as evidence for this theme. Do not drift into Support / Mentoring unless the selected theme is Support / Mentoring.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Select up to 3 exact positive student comments and up to 3 exact critical student comments from the responses. Use verbatim text only; do not invent comments.
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


def build_prompt(theme_name: str, docs: list[str], custom_prompt: str = "") -> str:
    if custom_prompt.strip():
        prompt = (
            custom_prompt.replace("{theme_name}", theme_name)
            + f"\n\nTheme scope: {THEME_DEFINITIONS.get(theme_name, theme_name)}"
            + "\n\nResponses:\n"
        )
    else:
        prompt = default_prompt(theme_name)

    for doc in docs:
        prompt += f"- {doc}\n"
    return prompt


def parse_llm_json(result_text: str) -> dict:
    match = re.search(r"\{[\s\S]*\}", result_text)
    json_str = match.group(0) if match else result_text
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid JSON structure returned by model: {json_str[:150]}"
        ) from exc
