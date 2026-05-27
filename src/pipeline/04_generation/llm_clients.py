from typing import Protocol

import requests


class LocalModelConnectionError(RuntimeError):
    pass


class LLMClient(Protocol):
    def ensure_model_available(self, model_name: str, allow_download: bool = False) -> None:
        ...

    def generate_json(self, model_name: str, prompt: str, timeout: int = 600) -> str:
        ...

    def unload(self, model_name: str) -> None:
        ...


class OllamaClient:
    base_url = "http://localhost:11434"

    def ensure_model_available(self, model_name: str, allow_download: bool = False) -> None:
        try:
            tags_response = requests.get(f"{self.base_url}/api/tags", timeout=5)
        except requests.exceptions.ConnectionError as exc:
            raise LocalModelConnectionError(
                "Could not connect to Ollama. Start Ollama locally before generating insights."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError("Ollama did not respond while checking installed models.") from exc

        if tags_response.status_code != 200:
            raise RuntimeError(
                f"Ollama model check failed with status {tags_response.status_code}: {tags_response.text}"
            )

        models = tags_response.json().get("models", [])
        installed = {
            str(model.get("name") or model.get("model") or "").strip()
            for model in models
        }
        if model_name in installed:
            return

        if not allow_download:
            available = ", ".join(sorted(installed)) or "none"
            raise RuntimeError(
                f"Ollama model '{model_name}' is not installed. "
                f"Installed models: {available}. Run `ollama pull {model_name}` "
                "or enable model download in the UI."
            )

        pull_response = requests.post(
            f"{self.base_url}/api/pull",
            json={"name": model_name, "stream": False},
            timeout=1800,
        )
        if pull_response.status_code != 200:
            raise RuntimeError(
                f"Ollama could not pull '{model_name}' "
                f"(status {pull_response.status_code}): {pull_response.text}"
            )

    def generate_json(self, model_name: str, prompt: str, timeout: int = 600) -> str:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            raise LocalModelConnectionError(
                f"Could not connect to Ollama. Ensure Ollama is running locally with model '{model_name}'."
            ) from exc

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama returned status {response.status_code}: {response.text}"
            )
        return response.json().get("response", "{}")

    def unload(self, model_name: str) -> None:
        try:
            requests.post(
                f"{self.base_url}/api/generate",
                json={"model": model_name, "keep_alive": 0},
                timeout=10,
            )
        except Exception:
            pass


class LlamaCppClient:
    def ensure_model_available(self, model_name: str, allow_download: bool = False) -> None:
        raise NotImplementedError("llama.cpp generation client is not configured yet.")

    def generate_json(self, model_name: str, prompt: str, timeout: int = 600) -> str:
        raise NotImplementedError("llama.cpp generation client is not configured yet.")

    def unload(self, model_name: str) -> None:
        return None


def get_llm_client(provider: str = "ollama") -> LLMClient:
    selected = (provider or "ollama").strip().lower()
    if selected in {"ollama", "gemma"}:
        return OllamaClient()
    if selected in {"llama.cpp", "llamacpp", "llama-cpp"}:
        return LlamaCppClient()
    raise ValueError(f"Unsupported LLM provider: {provider}")
