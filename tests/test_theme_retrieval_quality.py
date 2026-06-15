from __future__ import annotations

from importlib import import_module
import json
import tempfile
import unittest
from unittest import mock

import chromadb
import numpy as np

from src.config.settings import (
    HIERARCHICAL_RAG_BATCH_DOCUMENTS,
    INSIGHT_CACHE_VERSION,
    LLM_CONTEXT_DOCUMENTS,
)
from src.config.themes import LOW_INFORMATION_THEME


retrieval = import_module("src.pipeline.03_retrieval.service")
generation = import_module("src.pipeline.04_generation.service")
cache_store = import_module("src.pipeline.04_generation.cache")
theme_classifier = import_module("src.pipeline.02_embedding.theme_classifier")


def _assignment(
    config,
    *,
    primary: str,
    candidates: list[str],
    ambiguous: bool,
) -> dict:
    metadata = {
        "response_quality": "substantive",
        "theme_primary": primary,
        "theme_primary_score": 0.9,
        "theme_primary_score_kind": config.score_kind,
        "theme_ambiguous": ambiguous,
        "theme_score_margin": 0.05 if ambiguous else 0.7,
        "theme_candidate_count": len(candidates),
        "theme_classification_method": config.method,
        "theme_embedding_model": config.embedding_model_id,
        "theme_reranker_model": config.reranker_model_id,
        "theme_classification_version": config.classification_version,
        "theme_taxonomy_version": config.taxonomy_version,
        "theme_ambiguity_score_margin": config.ambiguity_score_margin,
    }
    for position, theme in enumerate(candidates, start=1):
        prefix = f"theme_candidate_{position}"
        metadata[prefix] = theme
        metadata[f"{prefix}_score"] = 0.9 - (position * 0.05)
        metadata[f"{prefix}_embedding_similarity"] = 0.8 - (position * 0.05)
        metadata[f"{prefix}_embedding_distance"] = 0.2 + (position * 0.05)
        metadata[f"{prefix}_embedding_rank"] = position
    return metadata


class FakeLlmClient:
    def __init__(self) -> None:
        self.prompts = []

    def ensure_model_available(self, *_args, **_kwargs) -> None:
        return None

    def generate_json(self, _model, prompt, **_kwargs) -> str:
        self.prompts.append(prompt)
        return json.dumps(
            {
                "summary": "Theme summary.",
                "sentiments": [],
                "positive_comments": [],
                "critical_comments": [],
                "student_suggestions": [],
                "subthemes": [],
            }
        )

    def unload(self, _model) -> None:
        return None


class FakeEmbeddingModel:
    def __init__(self) -> None:
        self.calls = []

    def encode(self, value, **kwargs):
        self.calls.append((value, kwargs))
        return np.asarray([1.0, 0.0], dtype=np.float32)


class FakeReranker:
    def __init__(self) -> None:
        self.pairs = []

    def predict(self, pairs):
        self.pairs = list(pairs)
        return np.asarray(
            [float(index) for index in range(len(self.pairs))],
            dtype=np.float32,
        )


class PersistedThemeRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.client = chromadb.PersistentClient(path=self.temp_dir.name)
        self.config = retrieval.expected_classification_config("fake-model")
        metadata = {
            "hnsw:space": "cosine",
            "embedding_model": "fake-model",
            **self.config.collection_metadata(
                status=theme_classifier.CLASSIFICATION_STATUS_READY
            ),
        }
        self.collection = self.client.create_collection(
            "survey_responses",
            metadata=metadata,
        )
        documents = [
            "The teacher explains clearly.",
            "The teacher is helpful, but I also need mentor support.",
            "My study coach helps me plan.",
            "My mentor also explains difficult course material.",
            "The timetable is published too late.",
        ]
        assignments = [
            _assignment(
                self.config,
                primary="Teachers",
                candidates=[
                    "Teachers",
                    "Support / Mentoring",
                    "Content and Organisation",
                ],
                ambiguous=False,
            ),
            _assignment(
                self.config,
                primary="Teachers",
                candidates=[
                    "Teachers",
                    "Support / Mentoring",
                    "Content and Organisation",
                ],
                ambiguous=True,
            ),
            _assignment(
                self.config,
                primary="Support / Mentoring",
                candidates=[
                    "Support / Mentoring",
                    "Teachers",
                    "Engagement & Contact",
                ],
                ambiguous=False,
            ),
            _assignment(
                self.config,
                primary="Support / Mentoring",
                candidates=[
                    "Support / Mentoring",
                    "Teachers",
                    "Content and Organisation",
                ],
                ambiguous=True,
            ),
            _assignment(
                self.config,
                primary="Content and Organisation",
                candidates=[
                    "Content and Organisation",
                    "Engagement & Contact",
                    "Teachers",
                ],
                ambiguous=False,
            ),
        ]
        locations = ["A", "A", "B", "A", "B"]
        metadatas = [
            {**assignment, "location": location}
            for assignment, location in zip(assignments, locations)
        ]
        self.collection.add(
            ids=[f"doc_{index}" for index in range(len(documents))],
            documents=documents,
            metadatas=metadatas,
            embeddings=[
                [1.0, 0.0],
                [0.9, 0.1],
                [0.8, 0.2],
                [0.7, 0.3],
                [0.0, 1.0],
            ],
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        retrieval.clear_runtime_caches()

    def test_confident_answer_is_evidence_only_for_primary_theme(self) -> None:
        teachers = retrieval.collect_theme_documents(
            self.collection,
            "Teachers",
        )
        support = retrieval.collect_theme_documents(
            self.collection,
            "Support / Mentoring",
        )

        self.assertIn("The teacher explains clearly.", teachers["documents"])
        self.assertNotIn("The teacher explains clearly.", support["documents"])
        self.assertEqual(
            teachers["definite_documents"],
            ["The teacher explains clearly."],
        )

    def test_ambiguous_answer_is_evidence_for_both_candidates(self) -> None:
        teachers = retrieval.collect_theme_documents(
            self.collection,
            "Teachers",
        )
        support = retrieval.collect_theme_documents(
            self.collection,
            "Support / Mentoring",
        )
        ambiguous_document = (
            "The teacher is helpful, but I also need mentor support."
        )

        self.assertIn(ambiguous_document, teachers["ambiguous_documents"])
        self.assertIn(ambiguous_document, support["ambiguous_documents"])

    def test_ambiguous_answer_is_counted_once_under_primary_theme(self) -> None:
        distribution = retrieval.theme_distribution(self.collection)

        self.assertEqual(distribution["counts"]["Teachers"], 2)
        self.assertEqual(distribution["counts"]["Support / Mentoring"], 2)
        self.assertEqual(
            sum(distribution["counts"].values()),
            self.collection.count(),
        )
        self.assertEqual(sum(distribution["percentages"].values()), 100)

    def test_metadata_filters_apply_to_counts_and_evidence(self) -> None:
        result = retrieval.collect_theme_documents(
            self.collection,
            "Teachers",
            filters={"location": "A"},
        )

        self.assertEqual(result["total_filtered_documents"], 3)
        self.assertEqual(result["vector_relevant_count"], 2)
        self.assertEqual(
            result["ambiguous_documents"],
            [
                "The teacher is helpful, but I also need mentor support.",
                "My mentor also explains difficult course material.",
            ],
        )

    def test_predefined_summary_loads_neither_embedding_nor_reranker(self) -> None:
        client = FakeLlmClient()
        with (
            mock.patch.object(generation, "load_cache", return_value={}),
            mock.patch.object(generation, "save_cache"),
            mock.patch.object(generation, "get_llm_client", return_value=client),
            mock.patch.object(
                retrieval,
                "get_collection",
                return_value=self.collection,
            ),
            mock.patch.object(
                retrieval,
                "get_theme_embedding_model",
            ) as load_embedding,
            mock.patch.object(
                retrieval,
                "load_reranker_model",
            ) as load_reranker,
        ):
            payload = generation.generate_theme_summary(
                theme_name="Teachers",
                theme_query="Teachers",
                provider="test",
                llm_model="fake-llm",
            )

        load_embedding.assert_not_called()
        load_reranker.assert_not_called()
        self.assertEqual(payload["definite_evidence_count"], 1)
        self.assertEqual(payload["ambiguous_evidence_count"], 2)
        self.assertIn("Definite evidence:", client.prompts[0])
        self.assertIn("Ambiguous candidate evidence:", client.prompts[0])
        self.assertIn(
            "Ignore any candidate evidence that is not genuinely relevant",
            client.prompts[0],
        )

    def test_free_text_retrieval_still_uses_embedding_and_reranking(self) -> None:
        embedding_model = FakeEmbeddingModel()
        reranker = FakeReranker()
        with (
            mock.patch.object(
                retrieval,
                "get_theme_embedding_model",
                return_value=embedding_model,
            ),
            mock.patch.object(retrieval, "reranker_enabled", return_value=True),
            mock.patch.object(
                retrieval,
                "selected_reranker_model",
                return_value="fake-reranker",
            ),
            mock.patch.object(
                retrieval,
                "load_reranker_model",
                return_value=reranker,
            ),
        ):
            result = retrieval.collect_documents_by_query(
                self.collection,
                "planning support",
                n_results=2,
            )

        self.assertEqual(len(embedding_model.calls), 1)
        self.assertGreater(len(reranker.pairs), 0)
        self.assertEqual(len(result["documents"]), 2)

    def test_classification_settings_invalidate_stale_cache(self) -> None:
        current = self.config.cache_metadata()
        base = {
            "cache_version": INSIGHT_CACHE_VERSION,
            "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
            "hierarchical_batch_documents": HIERARCHICAL_RAG_BATCH_DOCUMENTS,
            **current,
        }
        with mock.patch.object(
            retrieval,
            "classification_cache_metadata",
            return_value=current,
        ):
            self.assertTrue(cache_store.cache_matches_generation_settings(base))
            for key, stale_value in {
                "theme_classification_version": -1,
                "theme_candidate_count": current["theme_candidate_count"] + 1,
                "theme_reranker_model": "different-reranker",
                "theme_ambiguity_score_margin": 99.0,
            }.items():
                with self.subTest(key=key):
                    stale = {**base, key: stale_value}
                    self.assertFalse(
                        cache_store.cache_matches_generation_settings(stale)
                    )

    def test_missing_classification_requires_fresh_build(self) -> None:
        legacy = self.client.create_collection(
            "legacy",
            metadata={"embedding_model": "fake-model"},
        )
        with self.assertRaisesRegex(RuntimeError, "fresh vector build"):
            retrieval.validate_theme_classification(legacy)

    def test_low_information_theme_is_rejected_before_generation(self) -> None:
        with self.assertRaisesRegex(ValueError, "excluded from LLM generation"):
            generation._ensure_llm_eligible_theme(LOW_INFORMATION_THEME)


if __name__ == "__main__":
    unittest.main()
