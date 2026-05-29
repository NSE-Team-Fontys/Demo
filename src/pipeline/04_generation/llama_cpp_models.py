from dataclasses import dataclass
from typing import Any


DEFAULT_QUANTIZATION = "UD-Q4_K_XL"


@dataclass(frozen=True)
class LlamaCppGenerationSettings:
    context_size: int = 8192
    max_tokens: int = 8192
    temperature: float = 0.1
    top_k: int | None = 40
    top_p: float | None = None
    min_p: float | None = None
    repeat_penalty: float | None = None
    enable_thinking: bool = False
    json_mode: bool = True

    @property
    def server_args(self) -> list[str]:
        args: list[str] = []
        if self.context_size > 0:
            args.extend(["-c", str(self.context_size)])
        return args

    def chat_completion_payload(self, model_id: str, prompt: str) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "chat_template_kwargs": {"enable_thinking": self.enable_thinking},
        }
        if self.top_k is not None:
            payload["top_k"] = self.top_k
        if self.top_p is not None:
            payload["top_p"] = self.top_p
        if self.min_p is not None:
            payload["min_p"] = self.min_p
        if self.repeat_penalty is not None:
            payload["repeat_penalty"] = self.repeat_penalty
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        return payload

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_size": self.context_size,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "min_p": self.min_p,
            "repeat_penalty": self.repeat_penalty,
            "enable_thinking": self.enable_thinking,
            "json_mode": self.json_mode,
        }


@dataclass(frozen=True)
class LlamaCppModel:
    id: str
    name: str
    repo_id: str
    filename: str
    quantization: str = DEFAULT_QUANTIZATION
    size: str = ""
    speed: str = ""
    recommended: bool = False
    generation: LlamaCppGenerationSettings = LlamaCppGenerationSettings()

    @property
    def llama_server_model_id(self) -> str:
        return f"{self.repo_id}:{self.quantization}"

    @property
    def download_command(self) -> str:
        return " ".join(
            ["llama-server", "-hf", self.llama_server_model_id, *self.generation.server_args]
        )

    def server_command(self, server_bin: str) -> list[str]:
        return [server_bin, "-hf", self.llama_server_model_id, *self.generation.server_args]

    def chat_completion_payload(self, prompt: str) -> dict[str, Any]:
        return self.generation.chat_completion_payload(self.id, prompt)


GEMMA_LLAMA_CPP_MODELS = (
    LlamaCppModel(
        id="unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL",
        name="Gemma 4 E2B IT UD-Q4_K_XL",
        repo_id="unsloth/gemma-4-E2B-it-GGUF",
        filename="gemma-4-E2B-it-UD-Q4_K_XL.gguf",
        size="3.18 GB",
        speed="Very fast",
        generation=LlamaCppGenerationSettings(
            context_size=32000,
            max_tokens=8192,
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            enable_thinking=True,
        ),
    ),
    LlamaCppModel(
        id="unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL",
        name="Gemma 4 E4B IT UD-Q4_K_XL",
        repo_id="unsloth/gemma-4-E4B-it-GGUF",
        filename="gemma-4-E4B-it-UD-Q4_K_XL.gguf",
        size="~5 GB",
        speed="Fast",
        recommended=True,
        generation=LlamaCppGenerationSettings(
            context_size=32000,
            max_tokens=8192,
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            enable_thinking=True,
        ),
    ),
    LlamaCppModel(
        id="unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M",
        name="Gemma 4 26B A4B IT UD-Q4_K_M",
        repo_id="unsloth/gemma-4-26B-A4B-it-GGUF",
        filename="gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
        quantization="UD-Q4_K_M",
        size="~16.9 GB",
        speed="Moderate",
        generation=LlamaCppGenerationSettings(
            context_size=32000,
            max_tokens=8192,
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            enable_thinking=True,
        ),
    ),
    LlamaCppModel(
        id="unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL",
        name="Gemma 4 31B IT UD-Q4_K_XL",
        repo_id="unsloth/gemma-4-31B-it-GGUF",
        filename="gemma-4-31B-it-UD-Q4_K_XL.gguf",
        size="18.8 GB",
        speed="Slow",
        generation=LlamaCppGenerationSettings(
            context_size=32000,
            max_tokens=8192,
            temperature=1.0,
            top_p=0.95,
            top_k=64,
            enable_thinking=True,
        ),
    ),
)

LLAMA_CPP_MODEL_REGISTRY = {
    model.id: model for model in GEMMA_LLAMA_CPP_MODELS
}

LLAMA_CPP_MODEL_ALIASES = {
    "gemma4:e2b": "unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL",
    "gemma4:e4b": "unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL",
    "gemma4:26b": "unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M",
    "gemma4:31b": "unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL",
    "unsloth/gemma-4-E2B-it-GGUF:Q4_K_M": "unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL",
    "unsloth/gemma-4-E4B-it-GGUF:Q4_K_M": "unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL",
    "unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_M": "unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M",
    "unsloth/gemma-4-31B-it-GGUF:Q4_K_M": "unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL",
}


def resolve_llama_cpp_model(model_name: str) -> LlamaCppModel:
    selected = (model_name or "").strip()
    selected = LLAMA_CPP_MODEL_ALIASES.get(selected, selected)
    if selected in LLAMA_CPP_MODEL_REGISTRY:
        return LLAMA_CPP_MODEL_REGISTRY[selected]
    raise ValueError(
        f"Unsupported llama.cpp model '{model_name}'. "
        f"Choose one of: {', '.join(LLAMA_CPP_MODEL_REGISTRY)}."
    )


def llama_cpp_model_options() -> list[dict]:
    return [
        {
            "id": model.id,
            "name": model.name,
            "repo_id": model.repo_id,
            "filename": model.filename,
            "quantization": model.quantization,
            "size": model.size,
            "speed": model.speed,
            "recommended": model.recommended,
            "llama_server_model_id": model.llama_server_model_id,
            "download_command": model.download_command,
            "generation": model.generation.to_dict(),
        }
        for model in GEMMA_LLAMA_CPP_MODELS
    ]
