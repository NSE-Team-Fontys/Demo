from __future__ import annotations

from importlib import import_module
import unittest
from unittest import mock


llm_clients = import_module("src.pipeline.04_generation.llm_clients")

E2B_MODEL = "unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL"
E4B_MODEL = "unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL"


class LlamaCppClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = llm_clients.LlamaCppClient()

    def test_model_ids_supports_openai_and_models_payloads(self) -> None:
        self.assertEqual(
            self.client._model_ids({"data": [{"id": E4B_MODEL}]}),
            {E4B_MODEL},
        )
        self.assertEqual(
            self.client._model_ids({"models": [{"model": E2B_MODEL}]}),
            {E2B_MODEL},
        )

    def test_matching_single_server_model_is_reused(self) -> None:
        with (
            mock.patch.object(self.client, "_get_router_models", return_value=None),
            mock.patch.object(
                self.client, "_single_server_model_ids", return_value={E4B_MODEL}
            ),
            mock.patch.object(self.client, "_restart_llama_server") as restart,
        ):
            self.client.ensure_model_available(E4B_MODEL, allow_download=True)

        restart.assert_not_called()

    def test_different_single_server_model_is_restarted(self) -> None:
        with (
            mock.patch.object(self.client, "_get_router_models", return_value=None),
            mock.patch.object(
                self.client, "_single_server_model_ids", return_value={E4B_MODEL}
            ),
            mock.patch.object(self.client, "_restart_llama_server") as restart,
        ):
            self.client.ensure_model_available(E2B_MODEL, allow_download=True)

        restart.assert_called_once_with(E2B_MODEL)

    def test_different_single_server_model_errors_without_autostart(self) -> None:
        with (
            mock.patch.object(self.client, "_get_router_models", return_value=None),
            mock.patch.object(
                self.client, "_single_server_model_ids", return_value={E4B_MODEL}
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "not the selected model"):
                self.client.ensure_model_available(E2B_MODEL, allow_download=False)

    def test_models_endpoint_switches_an_app_managed_single_server(self) -> None:
        with (
            mock.patch.object(
                self.client,
                "_get_router_models",
                return_value=[{"id": E4B_MODEL}],
            ),
            mock.patch.object(self.client, "_has_managed_server", return_value=True),
            mock.patch.object(self.client, "_restart_llama_server") as restart,
        ):
            self.client.ensure_model_available(E2B_MODEL, allow_download=True)

        restart.assert_called_once_with(E2B_MODEL)

    def test_orphaned_configured_server_is_recovered_after_flask_restart(self) -> None:
        with (
            mock.patch.object(llm_clients.LlamaCppClient, "_managed_process", None),
            mock.patch.object(
                llm_clients.LlamaCppClient, "_saved_managed_pid", return_value=None
            ),
            mock.patch.object(
                llm_clients.LlamaCppClient,
                "_configured_server_pids",
                return_value=[1234],
            ),
        ):
            self.assertTrue(self.client._has_managed_server())


if __name__ == "__main__":
    unittest.main()
