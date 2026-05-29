from dataclasses import dataclass


DEFAULT_QUANTIZATION = "UD-Q4_K_XL"


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

    @property
    def llama_server_model_id(self) -> str:
        return f"{self.repo_id}:{self.quantization}"

    @property
    def download_command(self) -> str:
        return f"llama-server -hf {self.llama_server_model_id}"


GEMMA_LLAMA_CPP_MODELS = (
    LlamaCppModel(
        id="unsloth/gemma-4-E2B-it-GGUF:UD-Q4_K_XL",
        name="Gemma 4 E2B IT UD-Q4_K_XL",
        repo_id="unsloth/gemma-4-E2B-it-GGUF",
        filename="gemma-4-E2B-it-UD-Q4_K_XL.gguf",
        size="3.18 GB",
        speed="Very fast",
    ),
    LlamaCppModel(
        id="unsloth/gemma-4-E4B-it-GGUF:UD-Q4_K_XL",
        name="Gemma 4 E4B IT UD-Q4_K_XL",
        repo_id="unsloth/gemma-4-E4B-it-GGUF",
        filename="gemma-4-E4B-it-UD-Q4_K_XL.gguf",
        size="~5 GB",
        speed="Fast",
        recommended=True,
    ),
    LlamaCppModel(
        id="unsloth/gemma-4-26B-A4B-it-GGUF:UD-Q4_K_M",
        name="Gemma 4 26B A4B IT UD-Q4_K_M",
        repo_id="unsloth/gemma-4-26B-A4B-it-GGUF",
        filename="gemma-4-26B-A4B-it-UD-Q4_K_M.gguf",
        quantization="UD-Q4_K_M",
        size="~16.9 GB",
        speed="Moderate",
    ),
    LlamaCppModel(
        id="unsloth/gemma-4-31B-it-GGUF:UD-Q4_K_XL",
        name="Gemma 4 31B IT UD-Q4_K_XL",
        repo_id="unsloth/gemma-4-31B-it-GGUF",
        filename="gemma-4-31B-it-UD-Q4_K_XL.gguf",
        size="18.8 GB",
        speed="Slow",
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
        }
        for model in GEMMA_LLAMA_CPP_MODELS
    ]
