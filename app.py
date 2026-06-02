import threading
import src.config.runtime  # noqa: F401
from flask import Flask
from flask_cors import CORS

from src.api import register_blueprints
from src.config.settings import DEFAULT_LLM_PROVIDER, DEFAULT_LLM_MODEL


def _autostart_llm():
    try:
        from importlib import import_module
        llm_clients = import_module("src.pipeline.04_generation.llm_clients")
        provider = DEFAULT_LLM_PROVIDER.strip().lower()
        if provider not in {"llama.cpp", "llamacpp", "llama-cpp"}:
            return
        client = llm_clients.get_llm_client(DEFAULT_LLM_PROVIDER)
        client.ensure_model_available(DEFAULT_LLM_MODEL, allow_download=True)
        print("[LLM] llama-server started and ready.")
    except Exception as exc:
        print(f"[LLM] Auto-start skipped: {exc}")


def create_app():
    app = Flask(__name__)
    CORS(app)
    register_blueprints(app)
    threading.Thread(target=_autostart_llm, daemon=True).start()
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5001, threaded=True, use_reloader=False)
