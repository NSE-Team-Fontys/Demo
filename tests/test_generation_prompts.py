from __future__ import annotations

from importlib import import_module
import unittest


prompts = import_module("src.pipeline.04_generation.prompts")


class PromptParsingTests(unittest.TestCase):
    def test_parse_llm_json_repairs_truncated_object_with_trailing_comma(self) -> None:
        text = (
            '{ "summary": "...", '
            '"positive_comments": ["..."], '
            '"critical_comments": ["..."], '
            '"student_suggestions": ["..."], '
            '"subthemes": ["...", "..."],'
        )

        parsed = prompts.parse_llm_json(text)

        self.assertEqual(parsed["summary"], "...")
        self.assertEqual(parsed["subthemes"], ["...", "..."])

    def test_parse_llm_json_repairs_truncated_object_after_leading_text(self) -> None:
        text = 'Here is the JSON:\n{ "summary": "ok", "subthemes": ["one"],'

        parsed = prompts.parse_llm_json(text)

        self.assertEqual(parsed["summary"], "ok")
        self.assertEqual(parsed["subthemes"], ["one"])


if __name__ == "__main__":
    unittest.main()
