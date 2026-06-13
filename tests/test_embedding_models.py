from __future__ import annotations

from importlib import import_module
import unittest
from unittest import mock


embedding_models = import_module("src.pipeline.02_embedding.embedding_models")
reranker_models = import_module("src.pipeline.03_retrieval.reranker_models")


class EmbeddingModelCleanupTests(unittest.TestCase):
    def test_unload_clears_model_cache_and_device_memory(self) -> None:
        fake_torch = mock.Mock()
        fake_torch.backends.mps.is_available.return_value = True
        fake_torch.cuda.is_available.return_value = True

        with (
            mock.patch.object(
                embedding_models._load_embedding_model_cached,
                "cache_clear",
            ) as cache_clear,
            mock.patch.object(embedding_models.gc, "collect") as collect,
            mock.patch.dict("sys.modules", {"torch": fake_torch}),
        ):
            embedding_models.unload_embedding_models()

        cache_clear.assert_called_once_with()
        collect.assert_called_once_with()
        fake_torch.mps.empty_cache.assert_called_once_with()
        fake_torch.cuda.empty_cache.assert_called_once_with()

    def test_reranker_unload_clears_model_cache_and_device_memory(self) -> None:
        fake_torch = mock.Mock()
        fake_torch.backends.mps.is_available.return_value = True
        fake_torch.cuda.is_available.return_value = True

        with (
            mock.patch.object(
                reranker_models._load_reranker_model_cached,
                "cache_clear",
            ) as cache_clear,
            mock.patch.object(reranker_models.gc, "collect") as collect,
            mock.patch.dict("sys.modules", {"torch": fake_torch}),
        ):
            reranker_models.unload_reranker_models()

        cache_clear.assert_called_once_with()
        collect.assert_called_once_with()
        fake_torch.mps.empty_cache.assert_called_once_with()
        fake_torch.cuda.empty_cache.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
