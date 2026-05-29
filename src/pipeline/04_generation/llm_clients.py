import atexit
import shutil
import subprocess
import time
from typing import Protocol

import requests

from src.config.paths import ROOT_DIR
from src.config.settings import (
    DEFAULT_LLM_PROVIDER,
    LLAMA_CPP_API_KEY,
    LLAMA_CPP_BASE_URL,
    LLAMA_CPP_SERVER_BIN,
    LLAMA_CPP_STARTUP_TIMEOUT,
)
from .llama_cpp_models import resolve_llama_cpp_model


class LocalModelConnectionError(RuntimeError):
    pass


class LLMClient(Protocol):
    def ensure_model_available(self, model_name: str, allow_download: bool = False) -> None:
        ...

    def generate_json(self, model_name: str, prompt: str, timeout: int = 600) -> str:
        ...

    def unload(self, model_name: str) -> None:
        ...


class LlamaCppClient:
    base_url = LLAMA_CPP_BASE_URL.rstrip("/")
    _managed_process: subprocess.Popen | None = None
    _managed_log_path = ROOT_DIR / "logs" / "llama-server.log"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {LLAMA_CPP_API_KEY}",
            "Content-Type": "application/json",
        }

    def _server_command(self, model_name: str) -> list[str]:
        model = resolve_llama_cpp_model(model_name)
        return model.server_command(LLAMA_CPP_SERVER_BIN)

    def _check_llama_server_binary(self) -> None:
        if shutil.which(LLAMA_CPP_SERVER_BIN):
            return
        raise RuntimeError(
            f"Could not find `{LLAMA_CPP_SERVER_BIN}` on PATH. Install llama.cpp "
            "or set LLAMA_CPP_SERVER_BIN to the full llama-server path."
        )

    def _wait_until_server_ready(self, model_name: str) -> None:
        deadline = time.monotonic() + LLAMA_CPP_STARTUP_TIMEOUT
        last_error = ""
        while time.monotonic() < deadline:
            process = self.__class__._managed_process
            if process is not None and process.poll() is not None:
                raise RuntimeError(
                    "llama-server exited before becoming ready. "
                    f"Check {self._managed_log_path} for startup details."
                )
            try:
                response = requests.get(f"{self.base_url}/v1/models", timeout=3)
                if response.status_code == 200:
                    return
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            except requests.exceptions.RequestException as exc:
                last_error = str(exc)
            time.sleep(1)

        command = " ".join(self._server_command(model_name))
        raise RuntimeError(
            f"Timed out waiting for llama-server after {LLAMA_CPP_STARTUP_TIMEOUT}s. "
            f"Command: `{command}`. Last check: {last_error}. "
            f"Log: {self._managed_log_path}"
        )

    def _start_llama_server(self, model_name: str) -> None:
        process = self.__class__._managed_process
        if process is not None and process.poll() is None:
            self._wait_until_server_ready(model_name)
            return

        self._check_llama_server_binary()
        self._managed_log_path.parent.mkdir(parents=True, exist_ok=True)
        command = self._server_command(model_name)
        with self._managed_log_path.open("ab") as log_file:
            log_file.write(
                f"\n\n--- Starting {' '.join(command)} at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n".encode()
            )
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        self.__class__._managed_process = process
        self._wait_until_server_ready(model_name)

    def _model_command_hint(self, model_name: str) -> str:
        model = resolve_llama_cpp_model(model_name)
        return (
            f"Run `{model.download_command}` manually, or enable "
            "`Start llama-server if needed` in the UI."
        )

    def _get_router_models(self) -> list[dict] | None:
        response = requests.get(f"{self.base_url}/models?reload=1", timeout=10)
        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise RuntimeError(
                f"llama.cpp model check failed with status {response.status_code}: {response.text}"
            )
        return response.json().get("data", [])

    def ensure_model_available(self, model_name: str, allow_download: bool = False) -> None:
        model = resolve_llama_cpp_model(model_name)
        try:
            router_models = self._get_router_models()
        except requests.exceptions.ConnectionError as exc:
            if allow_download:
                self._start_llama_server(model.id)
                return
            raise LocalModelConnectionError(
                f"Could not connect to llama.cpp at {self.base_url}. "
                f"{self._model_command_hint(model.id)}"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError("llama.cpp did not respond while checking models.") from exc

        if router_models is None:
            try:
                models_response = requests.get(f"{self.base_url}/v1/models", timeout=10)
            except requests.exceptions.ConnectionError as exc:
                raise LocalModelConnectionError(
                    f"Could not connect to llama.cpp at {self.base_url}. "
                    "Start `llama-server` before generating insights."
                ) from exc
            if models_response.status_code != 200:
                raise RuntimeError(
                    f"llama.cpp /v1/models failed with status {models_response.status_code}: "
                    f"{models_response.text}"
                )
            return

        available = {
            str(item.get("id") or item.get("model") or "").strip(): item
            for item in router_models
        }
        if model.id in available:
            status = available[model.id].get("status") or {}
            if status.get("failed"):
                raise RuntimeError(
                    f"llama.cpp failed to load '{model.id}'. "
                    f"Status: {status}. {self._model_command_hint(model.id)}"
                )
            return

        installed = ", ".join(sorted(available)) or "none"
        raise RuntimeError(
            f"llama.cpp model '{model.id}' is not available to the router. "
            f"Available models: {installed}. {self._model_command_hint(model.id)}"
        )

    def generate_json(self, model_name: str, prompt: str, timeout: int = 600) -> str:
        model = resolve_llama_cpp_model(model_name)
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self._headers(),
                json=model.chat_completion_payload(prompt),
                timeout=timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise LocalModelConnectionError(
                f"Could not connect to llama.cpp at {self.base_url}. "
                f"Ensure `llama-server` is running with model '{model.id}'."
            ) from exc

        if response.status_code != 200:
            raise RuntimeError(
                f"llama.cpp returned status {response.status_code}: {response.text}"
            )
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return "{}"
        message = choices[0].get("message") or {}
        return message.get("content") or "{}"

    def unload(self, model_name: str) -> None:
        try:
            model = resolve_llama_cpp_model(model_name)
            requests.post(
                f"{self.base_url}/models/unload",
                headers=self._headers(),
                json={"model": model.id},
                timeout=10,
            )
        except Exception:
            pass
        self._stop_managed_server()

    @classmethod
    def _stop_managed_server(cls) -> None:
        process = cls._managed_process
        if process is None:
            return
        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            except Exception:
                pass
        cls._managed_process = None


atexit.register(LlamaCppClient._stop_managed_server)


def get_llm_client(provider: str = DEFAULT_LLM_PROVIDER) -> LLMClient:
    selected = (provider or DEFAULT_LLM_PROVIDER).strip().lower()
    if selected in {"llama.cpp", "llamacpp", "llama-cpp"}:
        return LlamaCppClient()
    raise ValueError(f"Unsupported LLM provider: {provider}")
