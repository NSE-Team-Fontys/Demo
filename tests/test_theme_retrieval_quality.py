from importlib import import_module
import unittest
from unittest import mock

import numpy as np

from src.config.themes import (
    LOW_INFORMATION_THEME,
    THEME_RETRIEVAL_PROMPT,
    THEMES_LIST,
)


retrieval = import_module("src.pipeline.03_retrieval.service")
generation = import_module("src.pipeline.04_generation.service")


class FakeCollection:
    metadata = {"embedding_model": "fake-model"}

    def __init__(self) -> None:
        self.rows = [
            ("low", "okay", {}),
            ("teacher", "De docent legt de stof duidelijk uit.", {}),
            ("content", "Het rooster wordt te laat gepubliceerd.", {}),
        ]

    def get(self, **_kwargs):
        return {
            "ids": [row[0] for row in self.rows],
            "documents": [row[1] for row in self.rows],
            "metadatas": [row[2] for row in self.rows],
        }

    def query(self, *, query_embeddings, include, **_kwargs):
        theme = query_embeddings[0]
        distances = {
            "Teachers": [0.01, 0.10, 0.70],
            "Content and Organisation": [0.80, 0.60, 0.10],
        }.get(theme, [0.90, 0.90, 0.90])
        result = {
            "ids": [[row[0] for row in self.rows]],
            "distances": [distances],
        }
        if "documents" in include:
            result["documents"] = [[row[1] for row in self.rows]]
        if "metadatas" in include:
            result["metadatas"] = [[row[2] for row in self.rows]]
        return result


class ThemeRetrievalQualityTests(unittest.TestCase):
    def tearDown(self) -> None:
        retrieval._theme_query_embeddings.clear()

    def test_theme_embeddings_use_task_prompt_and_skip_sink_theme(self) -> None:
        model = mock.Mock()
        model.encode.return_value = np.zeros(
            (len(retrieval.SUBSTANTIVE_THEMES), 3),
            dtype=np.float32,
        )

        with mock.patch.object(
            retrieval,
            "get_theme_embedding_model",
            return_value=model,
        ):
            embeddings = retrieval.get_theme_query_embeddings("test-model")

        self.assertEqual(set(embeddings), set(retrieval.SUBSTANTIVE_THEMES))
        self.assertNotIn(LOW_INFORMATION_THEME, embeddings)
        encoded_texts = model.encode.call_args.args[0]
        self.assertEqual(len(encoded_texts), len(retrieval.SUBSTANTIVE_THEMES))
        self.assertEqual(
            model.encode.call_args.kwargs,
            {
                "prompt": THEME_RETRIEVAL_PROMPT,
                "normalize_embeddings": True,
            },
        )

    def test_low_information_response_cannot_be_assigned_to_teachers(self) -> None:
        collection = FakeCollection()
        fake_embeddings = {theme: theme for theme in THEMES_LIST}

        with mock.patch.object(
            retrieval,
            "get_theme_query_embeddings",
            return_value=fake_embeddings,
        ):
            result = retrieval.collect_theme_documents(collection, "Teachers")

        self.assertEqual(
            result["documents"],
            ["De docent legt de stof duidelijk uit."],
        )
        self.assertEqual(result["counts"]["Teachers"], 1)
        self.assertEqual(result["counts"]["Content and Organisation"], 1)
        self.assertEqual(result["counts"][LOW_INFORMATION_THEME], 1)

    def test_reserved_theme_returns_only_low_information_responses(self) -> None:
        result = retrieval.collect_theme_documents(
            FakeCollection(),
            LOW_INFORMATION_THEME,
        )

        self.assertEqual(result["documents"], ["okay"])
        self.assertEqual(result["vector_relevant_count"], 1)
        self.assertEqual(result["frequency"], 33)

    def test_sink_theme_is_rejected_before_llm_generation(self) -> None:
        with self.assertRaisesRegex(ValueError, "excluded from LLM generation"):
            generation._ensure_llm_eligible_theme(LOW_INFORMATION_THEME)


if __name__ == "__main__":
    unittest.main()
