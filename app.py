from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

import csv
import os

import pandas as pd
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

# Fix for macOS (Apple Silicon) deadlocks when using HuggingFace models in Flask threads
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
import re

import chromadb
import requests

from anonymizer import process_file_with_layers
from src.core.embedding_models import (
    DEFAULT_EMBEDDING_MODEL,
    describe_embedding_runtime,
    load_embedding_model,
)
from src.core.reranker_models import (
    describe_reranker_runtime,
    load_reranker_model,
    reranker_enabled,
    selected_reranker_model,
)
from vector_builder import build_vector_db_stream

app = Flask(__name__)
# Enable CORS so your React app (localhost:5173) can talk to this API (localhost:5001)
CORS(app)

UPLOAD_FILE = "data/temp_upload.csv"
VECTOR_DB_PATH = Path("./survey_vector_db")
TEMP_DIR = Path("./temp")
ANONYMIZED_CSV_PATH = Path("./data/anonymized_survey.csv")
SEP_FILE = Path("./data/detected_sep.txt")
THEME_EMBEDDING_MODEL = DEFAULT_EMBEDDING_MODEL
RERANKER_CANDIDATE_MULTIPLIER = int(
    os.environ.get("RERANKER_CANDIDATE_MULTIPLIER", "5")
)
RERANKER_MAX_CANDIDATES = int(os.environ.get("RERANKER_MAX_CANDIDATES", "100"))
LLM_CONTEXT_DOCUMENTS = int(os.environ.get("LLM_CONTEXT_DOCUMENTS", "100"))
INSIGHT_CACHE_VERSION = 3
THEMES_LIST = [
    "Content and Organisation",
    "Professional Practice",
    "Teachers",
    "Support / Mentoring",
    "Examination & Assessment",
    "Engagement & Contact",
    "Special Circumstances",
]
THEME_DEFINITIONS = {
    "Content and Organisation": (
        "Curriculum content, course organization, planning, schedules, workload, "
        "study materials, module structure, learning objectives, and information "
        "about how the programme is arranged."
    ),
    "Professional Practice": (
        "Connection to professional practice, internships, industry projects, "
        "guest lectures, career readiness, workplace skills, practical assignments, "
        "and links with companies or the professional field."
    ),
    "Teachers": (
        "Lecturers and instructors, teaching quality, explanations, subject expertise, "
        "didactic skill, classroom teaching, teacher feedback, and teacher availability "
        "for learning-related questions."
    ),
    "Support / Mentoring": (
        "Mentors, study coaches, student advisors, counseling, personal guidance, "
        "wellbeing support, non-academic support, supervision, and mentoring."
    ),
    "Examination & Assessment": (
        "Exams, tests, assignments, grading, assessment criteria, rubrics, resits, "
        "assessment alignment, and feedback on assessed work."
    ),
    "Engagement & Contact": (
        "Student involvement, belonging, contact with classmates or staff, communication, "
        "student voice, feeling heard, class atmosphere, community, and participation."
    ),
    "Special Circumstances": (
        "Accommodations for disability, illness, caregiving, financial stress, accessibility, "
        "special personal circumstances, flexible arrangements, and study adjustments."
    ),
}
_theme_overview_cache = {}
_theme_embedding_models = {}
_theme_query_embeddings = {}
METADATA_COLS = {
    "ID",
    "Institution",
    "academic_year",
    "location",
    "programme",
    "study_mode",
    "cohort",
    "Jaar",
    "Actuele BRIN-code volgens RIO",
    "Actuele naam instelling volgens RIO",
    "Actuele CROHO-code volgens RIO",
    "Actuele Opleidingsnaam volgens RIO",
    "Actuele BRIN-volgnummer volgens RIO",
    "Type Student",
    "Opleidingsvorm (vt dt du)",
    "Leerroute_Track",
    "Studiejaar volgens instelling",
    "Kunstopleiding",
    "Afstandsonderwijs",
}

METADATA_ALIASES = {
    "institution": ["institution", "actuele naam instelling volgens rio"],
    "academic_year": ["academic_year", "jaar"],
    "location": ["location"],
    "programme": ["programme", "leerroute_track", "actuele opleidingsnaam volgens rio"],
    "study_mode": ["study_mode", "type student", "opleidingsvorm (vt dt du)"],
    "cohort": ["cohort", "studiejaar volgens instelling"],
}


def metadata_value(meta: dict, canonical_key: str):
    for key in METADATA_ALIASES.get(canonical_key, [canonical_key]):
        value = meta.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def filter_condition(canonical_key: str, value: str):
    aliases = METADATA_ALIASES.get(canonical_key, [canonical_key])
    conditions = [{key: value} for key in aliases]
    if len(conditions) == 1:
        return conditions[0]
    return {"$or": conditions}


def build_where_filter(filters: dict):
    if not filters:
        return None
    conditions = [filter_condition(key, value) for key, value in filters.items()]
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def clear_runtime_caches():
    _theme_overview_cache.clear()


def theme_overview_cache_key(filters: dict) -> tuple:
    return tuple(sorted(filters.items()))


def collection_embedding_model(collection) -> str:
    metadata = getattr(collection, "metadata", None) or {}
    return metadata.get("embedding_model") or THEME_EMBEDDING_MODEL


def get_theme_embedding_model(model_id: str | None = None):
    selected_model = model_id or THEME_EMBEDDING_MODEL
    if selected_model not in _theme_embedding_models:
        print(
            f"[EMBEDDINGS] Loading {selected_model} via "
            f"{describe_embedding_runtime(selected_model)}"
        )
        _theme_embedding_models[selected_model] = load_embedding_model(selected_model)
    return _theme_embedding_models[selected_model]


def theme_query_text(theme_name: str) -> str:
    definition = THEME_DEFINITIONS.get(theme_name)
    return f"{theme_name}. {definition}" if definition else theme_name


def get_theme_query_embeddings(model_id: str | None = None):
    selected_model = model_id or THEME_EMBEDDING_MODEL
    if selected_model not in _theme_query_embeddings:
        model = get_theme_embedding_model(selected_model)
        _theme_query_embeddings[selected_model] = {
            theme: model.encode(theme_query_text(theme), normalize_embeddings=True).tolist()
            for theme in THEMES_LIST
        }
    return _theme_query_embeddings[selected_model]


def rerank_documents(
    query: str,
    documents: list[str],
    *,
    metadatas: list[dict] | None = None,
    distances: list[float] | None = None,
    top_n: int | None = None,
    allow_model_download: bool = True,
) -> list[dict]:
    if not documents:
        return []

    if not reranker_enabled():
        ranked = []
        for i, doc in enumerate(documents):
            distance = distances[i] if distances and i < len(distances) else None
            similarity = max(0, 1 - distance) if distance is not None else None
            ranked.append(
                {
                    "document": doc,
                    "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                    "distance": distance,
                    "similarity": similarity,
                    "reranker_score": None,
                }
            )
        return ranked[:top_n] if top_n else ranked

    model_id = selected_reranker_model()
    print(f"[RERANKER] Loading {model_id} via {describe_reranker_runtime(model_id)}")
    model = load_reranker_model(model_id, allow_download=allow_model_download)
    pairs = [(query, doc) for doc in documents]
    scores = model.predict(pairs)

    ranked = []
    for i, (doc, score) in enumerate(zip(documents, scores)):
        distance = distances[i] if distances and i < len(distances) else None
        similarity = max(0, 1 - distance) if distance is not None else None
        ranked.append(
            {
                "document": doc,
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "distance": distance,
                "similarity": similarity,
                "reranker_score": float(score),
            }
        )

    ranked.sort(key=lambda item: item["reranker_score"], reverse=True)
    return ranked[:top_n] if top_n else ranked


def is_questionnaire_column(col: str) -> bool:
    name = str(col).strip()
    lower = name.lower()
    if name in METADATA_COLS or lower.startswith("themascore"):
        return False
    return (
        "?" in name
        or lower.startswith("wil jij")
        or lower.startswith("waarom")
        or lower.startswith("wat voor soort")
    )


def detect_sep(path: str) -> str:
    candidates = [",", ";", "\t"]
    try:
        with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as f:
            lines = []
            for _ in range(50):
                line = f.readline()
                if not line:
                    break
                if line.strip():
                    lines.append(line)
        if not lines:
            return ";"

        sample = "".join(lines)
        try:
            sniffed = csv.Sniffer().sniff(sample, delimiters="".join(candidates)).delimiter
            if sniffed in candidates:
                return sniffed
        except Exception:
            pass

        def score(delim: str) -> tuple[int, int, int]:
            counts = []
            bad = 0
            for ln in lines:
                try:
                    row = next(csv.reader([ln], delimiter=delim, quotechar='"', escapechar="\\"))
                    counts.append(len(row))
                except Exception:
                    bad += 1
            if not counts:
                return (0, -10_000, -1_000 - bad)
            mode = max(set(counts), key=counts.count)
            var = sum(abs(c - mode) for c in counts)
            return (mode, -var, -bad)

        return max(candidates, key=score)
    except Exception:
        return ";"


@app.route("/api/inspect-file", methods=["POST"])
def inspect_file():
    file = request.files.get("file")
    if not file:
        return jsonify({"status": "error", "error": "No file uploaded"})

    # Save the file temporarily
    Path(UPLOAD_FILE).parent.mkdir(parents=True, exist_ok=True)
    file.save(UPLOAD_FILE)

    try:
        sep = detect_sep(UPLOAD_FILE)
        SEP_FILE.parent.mkdir(parents=True, exist_ok=True)
        SEP_FILE.write_text(sep)

        # Read just the first few rows to get columns and a preview
        df = pd.read_csv(UPLOAD_FILE, sep=sep, nrows=5, encoding="utf-8-sig")
        preview_records = df.head(1).to_dict(orient="records")
        for rec in preview_records:
            for key, value in list(rec.items()):
                if pd.isna(value):
                    rec[key] = None

        return jsonify(
            {
                "status": "success",
                "columns": df.columns.tolist(),
                "preview": preview_records,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})


@app.route("/api/anonymize", methods=["POST"])
def anonymize():
    """Anonymize uploaded file with selected layers"""
    try:
        data = request.json
        selected_columns = data.get("selected_columns", [])
        selected_layers = data.get("selected_layers", ["presidio", "eu-pii"])

        input_file = Path(UPLOAD_FILE)
        output_file = ANONYMIZED_CSV_PATH

        if not input_file.exists():
            return jsonify({"status": "error", "error": "No file uploaded"}), 400

        sep = SEP_FILE.read_text().strip() if SEP_FILE.exists() else detect_sep(str(input_file))
        print(f"[ANONYMIZE] Columns: {selected_columns} | Layers: {selected_layers} | sep={repr(sep)}")

        return Response(
            process_file_with_layers(
                str(input_file),
                str(output_file),
                selected_columns,
                selected_layers,
                sep=sep,
            ),
            mimetype="application/x-ndjson",
        )

    except Exception as e:
        print(f"[ANONYMIZE ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/inspect-anonymized", methods=["GET"])
def inspect_anonymized():
    """Return the columns of the anonymized CSV so the frontend can let users pick which to vectorize."""
    try:
        if not ANONYMIZED_CSV_PATH.exists():
            return jsonify(
                {"status": "error", "error": "Anonymized CSV not found"}
            ), 400

        sep = detect_sep(str(ANONYMIZED_CSV_PATH))
        df = pd.read_csv(str(ANONYMIZED_CSV_PATH), sep=sep, nrows=0, encoding="utf-8-sig")
        all_columns = df.columns.tolist()

        # Questionnaire answer columns are the CSV headers that are actual questions.
        text_columns = [col for col in all_columns if is_questionnaire_column(col)]

        return jsonify(
            {
                "status": "success",
                "columns": all_columns,
                "text_columns": text_columns,
                "row_count": sum(
                    1 for _ in open(str(ANONYMIZED_CSV_PATH), encoding="utf-8")
                )
                - 1,
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/build-vectors", methods=["POST"])
def build_vectors():
    """Build vector database with proper metadata storage"""
    try:
        if not ANONYMIZED_CSV_PATH.exists():
            return jsonify(
                {"status": "error", "error": "Anonymized CSV not found"}
            ), 400

        data = request.json or {}
        embedding_model = str(data.get("embedding_model") or DEFAULT_EMBEDDING_MODEL).strip()
        selected_columns = data.get("selected_columns", None)
        allow_model_download = bool(data.get("allow_model_download", True))

        print(
            f"[BUILD-VECTORS] Starting vector DB build with model={embedding_model}, "
            f"columns={selected_columns}, allow_model_download={allow_model_download}"
        )

        # Clear the old AI insights cache so we generate fresh insights for the new data
        clear_runtime_caches()
        if CACHE_FILE.exists():
            try:
                CACHE_FILE.unlink()
            except Exception as e:
                print(f"Warning: Could not delete cache file: {e}")

        return Response(
            build_vector_db_stream(
                csv_path=str(ANONYMIZED_CSV_PATH),
                db_path=str(VECTOR_DB_PATH),
                embedding_model=embedding_model,
                selected_columns=selected_columns,
                allow_model_download=allow_model_download,
            ),
            mimetype="application/x-ndjson",
        )

    except Exception as e:
        print(f"[BUILD-VECTORS ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def status():
    anonymized_exists = os.path.exists(ANONYMIZED_CSV_PATH)
    vector_db_exists = os.path.exists("survey_vector_db") and any(
        os.scandir("survey_vector_db")
    )
    return jsonify(
        {
            "status": "success",
            "anonymized_exists": anonymized_exists,
            "vector_db_exists": vector_db_exists,
        }
    )


# ── QUERY VECTORS ────────────────────────────────────────────────────────────


@app.route("/api/filter-options", methods=["GET"])
def get_filter_options():
    """Get available filter options from the vector database metadata"""
    try:
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify({"status": "empty", "options": {}}), 200

        # Get all documents with metadata
        all_docs = collection.get(limit=collection.count())

        # Extract unique values from metadata
        institutions = set()
        years = set()
        locations = set()
        programmes = set()
        study_modes = set()
        cohorts = set()

        if all_docs["metadatas"]:
            for meta in all_docs["metadatas"]:
                value = metadata_value(meta, "institution")
                if value:
                    institutions.add(str(value))
                value = metadata_value(meta, "academic_year")
                if value:
                    years.add(str(value))
                value = metadata_value(meta, "location")
                if value:
                    locations.add(str(value))
                value = metadata_value(meta, "programme")
                if value:
                    programmes.add(str(value))
                value = metadata_value(meta, "study_mode")
                if value:
                    study_modes.add(str(value))
                value = metadata_value(meta, "cohort")
                if value:
                    cohorts.add(str(value))

        return jsonify(
            {
                "status": "success",
                "options": {
                    "institutions": sorted(list(institutions)),
                    "academic_years": sorted(list(years)),
                    "locations": sorted(list(locations)),
                    "programmes": sorted(list(programmes)),
                    "study_modes": sorted(list(study_modes)),
                    "cohorts": sorted(list(cohorts)),
                },
            }
        )

    except Exception as e:
        print(f"[FILTER OPTIONS ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/query-vectors", methods=["GET"])
def query_vectors():
    """Search vectors with metadata filtering"""
    try:
        query_text = request.args.get("query", "").strip()
        top_k = min(int(request.args.get("n", 10)), 50)

        if not query_text:
            return jsonify({"status": "error", "error": "Empty query"}), 400

        # Get filters from query params
        filters = {}
        if request.args.get("institution") and request.args.get("institution") != "all":
            filters["institution"] = request.args.get("institution")
        if (
            request.args.get("academic_year")
            and request.args.get("academic_year") != "all"
        ):
            filters["academic_year"] = request.args.get("academic_year")
        if request.args.get("location") and request.args.get("location") != "all":
            filters["location"] = request.args.get("location")
        if request.args.get("programme") and request.args.get("programme") != "all":
            filters["programme"] = request.args.get("programme")
        if request.args.get("study_mode") and request.args.get("study_mode") != "all":
            filters["study_mode"] = request.args.get("study_mode")
        if request.args.get("cohort") and request.args.get("cohort") != "all":
            filters["cohort"] = request.args.get("cohort")

        print(f"[QUERY] Searching: '{query_text}' | Filters: {filters}")

        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify(
                {
                    "status": "error",
                    "error": "Vector database not found. Build vectors first.",
                }
            ), 400

        embedding_model = collection_embedding_model(collection)
        model = get_theme_embedding_model(embedding_model)
        query_embedding = model.encode(query_text, normalize_embeddings=True)

        # Build where filter - support multiple conditions and metadata aliases.
        where_filter = None
        if filters:
            conditions = [filter_condition(key, value) for key, value in filters.items()]
            if len(conditions) > 1:
                where_filter = {"$and": conditions}
            else:
                where_filter = conditions[0]

        retrieval_k = min(
            max(top_k * RERANKER_CANDIDATE_MULTIPLIER, top_k),
            max(collection.count(), 1),
            RERANKER_MAX_CANDIDATES,
        )

        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=retrieval_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        formatted = []
        if results["documents"] and len(results["documents"]) > 0:
            ranked_results = rerank_documents(
                query_text,
                results["documents"][0],
                metadatas=results["metadatas"][0] if results["metadatas"] else None,
                distances=results["distances"][0] if results["distances"] else None,
                top_n=top_k,
            )
            for i, ranked in enumerate(ranked_results):
                doc = ranked["document"]
                similarity = ranked["similarity"] if ranked["similarity"] is not None else 0

                result_item = {
                    "id": i + 1,
                    "document": doc,
                    "preview": doc[:300] + "..." if len(doc) > 300 else doc,
                    "similarity": round(similarity, 3),
                    "percentage": round(similarity * 100, 1),
                    "reranker_score": ranked["reranker_score"],
                }

                if ranked["metadata"]:
                    result_item["metadata"] = ranked["metadata"]

                formatted.append(result_item)

        return jsonify(
            {
                "status": "success",
                "results": formatted,
                "count": len(formatted),
                "candidate_count": len(results["documents"][0])
                if results["documents"]
                else 0,
                "reranker": selected_reranker_model() if reranker_enabled() else None,
                "query": query_text,
                "filters_applied": filters,
            }
        )

    except Exception as e:
        print(f"[QUERY ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


CACHE_FILE = Path("./gemma_cache.json")


def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_cache(cache_data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)


def current_reranker_id():
    return selected_reranker_model() if reranker_enabled() else None


def cache_matches_generation_settings(cached_theme: dict) -> bool:
    return (
        cached_theme.get("cache_version") == INSIGHT_CACHE_VERSION
        and cached_theme.get("llm_context_documents") == LLM_CONTEXT_DOCUMENTS
        and cached_theme.get("reranker") == current_reranker_id()
    )


def subtheme_mention_rows(subthemes: list, docs: list) -> list:
    """Approximate each subtheme's share of detected subtheme mentions."""
    if not subthemes or not docs:
        return []

    stopwords = {
        "and",
        "the",
        "for",
        "with",
        "from",
        "that",
        "this",
        "over",
        "into",
        "aan",
        "een",
        "het",
        "van",
        "voor",
        "met",
        "naar",
    }
    normalized_docs = [str(doc).lower() for doc in docs]
    doc_words = [
        set(re.findall(r"[a-zA-ZÀ-ÿ0-9]+", doc))
        for doc in normalized_docs
    ]
    rows = []

    for subtheme in subthemes:
        label = str(subtheme).strip()
        if not label:
            continue

        label_norm = label.lower()
        tokens = [
            token
            for token in re.findall(r"[a-zA-ZÀ-ÿ0-9]+", label_norm)
            if len(token) > 3 and token not in stopwords
        ]
        token_roots = {token[:6] for token in tokens if len(token) > 6}

        mentions = 0
        for doc, words in zip(normalized_docs, doc_words):
            if (
                label_norm in doc
                or any(token in words for token in tokens)
                or any(any(word.startswith(root) for word in words) for root in token_roots)
            ):
                mentions += 1

        rows.append(
            {
                "subtheme": label,
                "mentions": mentions,
                "doc_percentage": int(round((mentions / len(docs)) * 100)),
                "percentage": 0,
            }
        )

    total_mentions = sum(row["mentions"] for row in rows)
    if total_mentions > 0:
        for row in rows:
            row["percentage"] = int(round((row["mentions"] / total_mentions) * 100))

    return rows


def percentages_from_counts(counts: dict[str, int]) -> dict[str, int]:
    """Convert theme counts to integer percentages that sum to exactly 100."""
    total = sum(max(0, int(counts.get(theme, 0))) for theme in THEMES_LIST)
    if total <= 0:
        return {theme: 0 for theme in THEMES_LIST}

    raw = {
        theme: (max(0, int(counts.get(theme, 0))) * 100) / total
        for theme in THEMES_LIST
    }
    percentages = {theme: int(raw[theme]) for theme in THEMES_LIST}
    remainder = 100 - sum(percentages.values())
    by_fraction = sorted(
        THEMES_LIST,
        key=lambda theme: (raw[theme] - percentages[theme], counts.get(theme, 0)),
        reverse=True,
    )

    for theme in by_fraction[:remainder]:
        percentages[theme] += 1

    return percentages


def theme_distribution(collection, model_id: str | None = None, where_filter=None) -> dict:
    """Assign each response to its closest hardcoded theme so totals equal 100%."""
    if where_filter:
        matching_docs = collection.get(where=where_filter)
        total_docs = (
            len(matching_docs["ids"])
            if matching_docs and matching_docs.get("ids")
            else 0
        )
    else:
        total_docs = collection.count()

    counts = {theme: 0 for theme in THEMES_LIST}
    if total_docs <= 0:
        return {
            "counts": counts,
            "percentages": percentages_from_counts(counts),
            "total_docs": 0,
        }

    theme_embeddings = get_theme_query_embeddings(model_id)
    best_by_doc = {}

    for theme_name in THEMES_LIST:
        results = collection.query(
            query_embeddings=[theme_embeddings[theme_name]],
            n_results=total_docs,
            where=where_filter,
            include=["distances"],
        )
        ids = results.get("ids", [[]])[0] if results.get("ids") else []
        distances = (
            results.get("distances", [[]])[0] if results.get("distances") else []
        )
        for doc_id, distance in zip(ids, distances):
            current = best_by_doc.get(doc_id)
            if current is None or distance < current[0]:
                best_by_doc[doc_id] = (distance, theme_name)

    for _, theme_name in best_by_doc.values():
        counts[theme_name] += 1

    return {
        "counts": counts,
        "percentages": percentages_from_counts(counts),
        "total_docs": total_docs,
    }


def ensure_ollama_model_available(model_name: str, allow_pull: bool = False) -> None:
    """Verify Ollama is running and the requested local model exists."""
    try:
        tags_response = requests.get("http://localhost:11434/api/tags", timeout=5)
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            "Could not connect to Ollama. Start Ollama locally before generating insights."
        ) from e
    except requests.exceptions.Timeout as e:
        raise RuntimeError("Ollama did not respond while checking installed models.") from e

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

    if not allow_pull:
        available = ", ".join(sorted(installed)) or "none"
        raise RuntimeError(
            f"Ollama model '{model_name}' is not installed. "
            f"Installed models: {available}. Run `ollama pull {model_name}` "
            "or enable model download in the UI."
        )

    pull_response = requests.post(
        "http://localhost:11434/api/pull",
        json={"name": model_name, "stream": False},
        timeout=1800,
    )
    if pull_response.status_code != 200:
        raise RuntimeError(
            f"Ollama could not pull '{model_name}' (status {pull_response.status_code}): {pull_response.text}"
        )


@app.route("/api/theme-summary", methods=["POST"])
def theme_summary():
    try:
        data = request.json
        theme_name = data.get("theme", "")
        theme_query = data.get("query", "")
        ollama_model = data.get("ollama_model", "gemma4:e4b")
        allow_model_download = bool(data.get("allow_model_download", False))
        theme_search_query = theme_query_text(theme_name) if theme_name else theme_query

        if not theme_search_query:
            return jsonify({"status": "error", "error": "No query provided"}), 400

        # ── Check cache FIRST — no Ollama round-trip needed for cached themes ──
        cache = load_cache()
        if theme_name in cache:
            print(f"[GEMMA4] Returning cached summary for: {theme_name}")
            cached_data = cache[theme_name]
            has_view_more_fields = (
                "positive_comments" in cached_data
                and "critical_comments" in cached_data
                and "student_suggestions" in cached_data
                and "subtheme_mentions" in cached_data
            )
            has_reranker_fields = (
                "vector_relevant_count" in cached_data
                and "llm_document_count" in cached_data
                and "reranker" in cached_data
            )
            if (
                has_view_more_fields
                and has_reranker_fields
                and cache_matches_generation_settings(cached_data)
            ):
                print(f"[GEMMA4] Returning cached summary for: {theme_name}")
                cached_data["status"] = "success"
                return jsonify(cached_data)
            print(
                f"[GEMMA4] Cached summary for {theme_name} is missing current "
                "dashboard fields; regenerating."
            )

        print(f"[GEMMA4] Cache miss — generating summary for: {theme_name}")
        ensure_ollama_model_available(ollama_model, allow_pull=allow_model_download)

        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        collection = client.get_collection("survey_responses")

        embedding_model = collection_embedding_model(collection)
        model = get_theme_embedding_model(embedding_model)
        query_embedding = model.encode(theme_search_query, normalize_embeddings=True)
        total_docs = collection.count()
        distribution = theme_distribution(collection, embedding_model)
        retrieval_k = min(
            max(20 * RERANKER_CANDIDATE_MULTIPLIER, 20),
            max(total_docs, 1),
            RERANKER_MAX_CANDIDATES,
        )

        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=retrieval_k,
            include=["documents", "distances"],
        )

        # Filter for first-stage vector relevance before reranking.
        relevant_docs = []
        relevant_distances = []
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i]
                relevant_docs.append(doc)
                relevant_distances.append(distance)

        vector_relevant_count = distribution["counts"].get(theme_name, len(relevant_docs))
        frequency = distribution["percentages"].get(theme_name, 0)
        ranked_docs = rerank_documents(
            theme_search_query,
            relevant_docs[:RERANKER_MAX_CANDIDATES],
            distances=relevant_distances[:RERANKER_MAX_CANDIDATES],
            top_n=RERANKER_MAX_CANDIDATES,
            allow_model_download=allow_model_download,
        )
        relevant_docs = [item["document"] for item in ranked_docs]
        llm_docs = relevant_docs[:LLM_CONTEXT_DOCUMENTS]

        # Real Gemma Call via Ollama

        theme_scope = THEME_DEFINITIONS.get(theme_name, theme_name)
        prompt = f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Theme scope: {theme_scope}
Only analyze comments as evidence for this theme. Do not drift into Support / Mentoring unless the selected theme is Support / Mentoring.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Select up to 3 exact positive student comments and up to 3 exact critical student comments from the responses. Use verbatim text only; do not invent comments.
Select up to 3 exact student suggestions where students propose a solution, improvement, or concrete next step instead of only complaining. Use verbatim text only; return an empty array if no clear suggestions exist.
Also extract 3 to 5 short sub-themes or topics mentioned (e.g. "Lecture Pacing", "Teacher Availability").
Respond EXACTLY in this JSON format:
{{
  "summary": "...",
  "sentiments": [
    {{"sentiment": "Positive", "point": "..."}}
  ],
  "positive_comments": ["..."],
  "critical_comments": ["..."],
  "student_suggestions": ["..."],
  "subthemes": ["...", "..."]
}}

Responses:
"""
        for doc in llm_docs:
            prompt += f"- {doc}\n"

        real_quotes = relevant_docs[:3] if len(relevant_docs) >= 3 else relevant_docs

        try:
            print(
                f"[GEMMA] Reranked {vector_relevant_count} relevant docs; "
                f"sending {len(llm_docs)} docs to local Ollama (gemma model)..."
            )
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                },
                timeout=120,
            )

            if response.status_code == 200:
                result_text = response.json().get("response", "{}")
                print(f"[GEMMA] Raw response received: {result_text}")

                # Attempt to extract a JSON block if wrapped in markdown
                match = re.search(r"\{[\s\S]*\}", result_text)
                json_str = match.group(0) if match else result_text

                try:
                    parsed = json.loads(json_str)
                except json.JSONDecodeError:
                    print("[GEMMA] Strict JSON parse failed. Raw string:", json_str)
                    raise Exception(
                        f"Invalid JSON structure returned by model: {json_str[:150]}"
                    )

                summary = parsed.get("summary", "Summary could not be parsed.")
                sentiments = parsed.get("sentiments", [])
                positive_comments = parsed.get("positive_comments", [])
                critical_comments = parsed.get("critical_comments", [])
                student_suggestions = parsed.get("student_suggestions", [])
                subthemes = parsed.get("subthemes", [])
            else:
                error_body = response.text
                raise Exception(
                    f"Ollama returned status {response.status_code}: {error_body}"
                )

        except requests.exceptions.ConnectionError:
            return jsonify(
                {
                    "status": "error",
                    "error": f"Could not connect to Ollama. Ensure Ollama is running locally with model '{ollama_model}'.",
                }
            ), 503
        except Exception as e:
            error_msg = str(e)
            print(f"[GEMMA ERROR] {error_msg}")
            return jsonify({"status": "error", "error": error_msg}), 500

        response_data = {
            "status": "success",
            "theme": theme_name,
            "frequency": frequency,
            "document_count": len(relevant_docs),
            "vector_relevant_count": vector_relevant_count,
            "llm_document_count": len(llm_docs),
            "cache_version": INSIGHT_CACHE_VERSION,
            "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
            "reranker": current_reranker_id(),
            "summary": summary,
            "sentiments": sentiments,
            "positive_comments": positive_comments[:3],
            "critical_comments": critical_comments[:3],
            "student_suggestions": student_suggestions[:3],
            "subthemes": subthemes,
            "subtheme_mentions": subtheme_mention_rows(subthemes, relevant_docs),
            "quotes": real_quotes,
        }

        # Only cache successful generations that have valid sentiments
        if sentiments and len(sentiments) > 0:
            cache[theme_name] = response_data
            save_cache(cache)
            print(f"[GEMMA4] Saved summary to cache for: {theme_name}")

        return jsonify(response_data)

    except Exception as e:
        print(f"[GEMMA4 ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/clear-cache", methods=["POST"])
def clear_cache():
    """Delete the gemma_cache.json file so insights are regenerated fresh."""
    try:
        clear_runtime_caches()
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        return jsonify({"status": "success", "message": "Cache cleared"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/precompute-insights", methods=["POST"])
def precompute_insights():
    """Stream NDJSON progress as we precompute insights for all themes."""
    data = request.json
    themes = data.get("themes", [])
    ollama_model = data.get("ollama_model", "gemma4:e4b")
    custom_prompt = data.get("custom_prompt", "")
    allow_model_download = bool(data.get("allow_model_download", False))

    if not themes:
        return jsonify({"error": "No themes provided"}), 400

    def generate():
        try:
            yield (
                json.dumps(
                    {
                        "status": "progress",
                        "progress": 1,
                        "message": f"Checking Ollama model '{ollama_model}'...",
                    }
                )
                + "\n"
            )
            ensure_ollama_model_available(
                ollama_model, allow_pull=allow_model_download
            )

            client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
            collection = client.get_collection("survey_responses")
            total_docs = collection.count()
            cache = load_cache()
            embedding_model = collection_embedding_model(collection)
            distribution = theme_distribution(collection, embedding_model)

            for i, theme in enumerate(themes):
                theme_name = theme.get("name")
                query = theme_query_text(theme_name)

                yield (
                    json.dumps(
                        {
                            "status": "progress",
                            "theme": theme_name,
                            "progress": int((i / len(themes)) * 100),
                            "message": f"Querying VectorDB for {theme_name}...",
                        }
                    )
                    + "\n"
                )

                model = get_theme_embedding_model(embedding_model)
                query_embedding = model.encode(query, normalize_embeddings=True)
                retrieval_k = min(RERANKER_MAX_CANDIDATES, max(total_docs, 1))

                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=retrieval_k,
                    include=["documents", "distances"],
                )

                relevant_docs = []
                relevant_distances = []
                if results["documents"] and len(results["documents"]) > 0:
                    for j, doc in enumerate(results["documents"][0]):
                        distance = results["distances"][0][j]
                        relevant_docs.append(doc)
                        relevant_distances.append(distance)

                vector_relevant_count = distribution["counts"].get(
                    theme_name, len(relevant_docs)
                )
                ranked_docs = rerank_documents(
                    query,
                    relevant_docs[:RERANKER_MAX_CANDIDATES],
                    distances=relevant_distances[:RERANKER_MAX_CANDIDATES],
                    top_n=RERANKER_MAX_CANDIDATES,
                    allow_model_download=allow_model_download,
                )
                relevant_docs = [item["document"] for item in ranked_docs]
                llm_docs = relevant_docs[:LLM_CONTEXT_DOCUMENTS]

                frequency = distribution["percentages"].get(theme_name, 0)

                # Check cache for summary
                cached_theme = cache.get(theme_name, {})
                cache_has_current_settings = cache_matches_generation_settings(
                    cached_theme
                )
                if (
                    theme_name in cache
                    and "summary" in cache[theme_name]
                    and cache[theme_name].get("sentiments")
                    and cache_has_current_settings
                ):
                    # Update frequency but keep summary
                    cache[theme_name]["frequency"] = frequency
                    cache[theme_name]["vector_relevant_count"] = vector_relevant_count
                    cache[theme_name]["llm_document_count"] = min(
                        len(relevant_docs), LLM_CONTEXT_DOCUMENTS
                    )
                    cache[theme_name]["cache_version"] = INSIGHT_CACHE_VERSION
                    cache[theme_name]["llm_context_documents"] = LLM_CONTEXT_DOCUMENTS
                    cache[theme_name]["reranker"] = current_reranker_id()
                    save_cache(cache)
                    yield (
                        json.dumps(
                            {
                                "status": "progress",
                                "theme": theme_name,
                                "progress": int(((i + 1) / len(themes)) * 100),
                                "message": f"Loaded cached insights for {theme_name}",
                            }
                        )
                        + "\n"
                    )
                    continue

                yield (
                    json.dumps(
                        {
                            "status": "progress",
                            "theme": theme_name,
                            "progress": int(((i + 0.5) / len(themes)) * 100),
                            "message": (
                                f"{ollama_model} is generating summary for "
                                f"{theme_name} with {len(llm_docs)} answers..."
                            ),
                        }
                    )
                    + "\n"
                )

                if not relevant_docs:
                    cache[theme_name] = {
                        "frequency": frequency,
                        "vector_relevant_count": vector_relevant_count,
                        "llm_document_count": 0,
                        "cache_version": INSIGHT_CACHE_VERSION,
                        "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
                        "reranker": current_reranker_id(),
                        "summary": "Not enough highly relevant responses found.",
                        "sentiments": [],
                    }
                    save_cache(cache)
                    continue

                # Use custom prompt if provided, otherwise use default
                if custom_prompt.strip():
                    prompt = (
                        custom_prompt.replace("{theme_name}", theme_name)
                        + f"\n\nTheme scope: {THEME_DEFINITIONS.get(theme_name, theme_name)}"
                        + "\n\nResponses:\n"
                    )
                else:
                    prompt = f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Theme scope: {THEME_DEFINITIONS.get(theme_name, theme_name)}
Only analyze comments as evidence for this theme. Do not drift into Support / Mentoring unless the selected theme is Support / Mentoring.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Select up to 3 exact positive student comments and up to 3 exact critical student comments from the responses. Use verbatim text only; do not invent comments.
Select up to 3 exact student suggestions where students propose a solution, improvement, or concrete next step instead of only complaining. Use verbatim text only; return an empty array if no clear suggestions exist.
Also extract 3 to 5 short sub-themes or topics mentioned.
Respond EXACTLY in this JSON format:
{{
  "summary": "...",
  "sentiments": [
    {{"sentiment": "Positive", "point": "..."}}
  ],
  "positive_comments": ["..."],
  "critical_comments": ["..."],
  "student_suggestions": ["..."],
  "subthemes": ["...", "..."]
}}

Responses:
"""
                for doc in llm_docs:
                    prompt += f"- {doc}\n"

                real_quotes = (
                    relevant_docs[:3] if len(relevant_docs) >= 3 else relevant_docs
                )

                try:
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": ollama_model,
                            "prompt": prompt,
                            "stream": False,
                            "format": "json",
                        },
                        timeout=120,
                    )

                    if response.status_code == 200:
                        result_text = response.json().get("response", "{}")
                        match = re.search(r"\{[\s\S]*\}", result_text)
                        json_str = match.group(0) if match else result_text
                        parsed = json.loads(json_str)

                        cache[theme_name] = {
                            "frequency": frequency,
                            "vector_relevant_count": vector_relevant_count,
                            "llm_document_count": len(llm_docs),
                            "cache_version": INSIGHT_CACHE_VERSION,
                            "llm_context_documents": LLM_CONTEXT_DOCUMENTS,
                            "reranker": current_reranker_id(),
                            "summary": parsed.get(
                                "summary", "Summary could not be parsed."
                            ),
                            "sentiments": parsed.get("sentiments", []),
                            "positive_comments": parsed.get(
                                "positive_comments", []
                            )[:3],
                            "critical_comments": parsed.get(
                                "critical_comments", []
                            )[:3],
                            "student_suggestions": parsed.get(
                                "student_suggestions", []
                            )[:3],
                            "subthemes": parsed.get("subthemes", []),
                            "subtheme_mentions": subtheme_mention_rows(
                                parsed.get("subthemes", []), relevant_docs
                            ),
                            "quotes": real_quotes,
                        }
                    else:
                        raise RuntimeError(
                            f"Ollama returned status {response.status_code}: {response.text}"
                        )
                except Exception as e:
                    yield (
                        json.dumps(
                            {
                                "status": "error",
                                "theme": theme_name,
                                "message": f"Failed to generate summary: {str(e)}",
                            }
                        )
                        + "\n"
                    )
                    return
                save_cache(cache)

            yield (
                json.dumps(
                    {
                        "status": "success",
                        "message": "All insights generated!",
                        "progress": 100,
                    }
                )
                + "\n"
            )

        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")


@app.route("/api/themes-overview", methods=["GET"])
def get_themes_overview():
    cache = {
        theme: data
        for theme, data in load_cache().items()
        if isinstance(data, dict) and cache_matches_generation_settings(data)
    }

    # Check for filters
    filters = {}
    for key in [
        "institution",
        "academic_year",
        "location",
        "programme",
        "study_mode",
        "cohort",
    ]:
        val = request.args.get(key)
        if val and val != "All":
            filters[key] = val

    if not filters:
        return jsonify(cache)

    # We have filters, dynamically calculate frequencies
    try:
        cache_key = theme_overview_cache_key(filters)
        if cache_key in _theme_overview_cache:
            return jsonify(_theme_overview_cache[cache_key])

        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        collection = client.get_collection("survey_responses")

        where_clause = build_where_filter(filters)

        # Total matching documents
        filtered_docs = collection.get(where=where_clause)
        total_docs = (
            len(filtered_docs["ids"]) if filtered_docs and filtered_docs["ids"] else 0
        )

        import copy

        new_cache = copy.deepcopy(cache)

        if total_docs == 0:
            for theme in new_cache:
                new_cache[theme]["frequency"] = 0
            _theme_overview_cache[cache_key] = new_cache
            return jsonify(new_cache)

        distribution = theme_distribution(
            collection,
            collection_embedding_model(collection),
            where_filter=where_clause,
        )
        for theme_name in THEMES_LIST:
            if theme_name not in new_cache:
                continue
            new_cache[theme_name]["frequency"] = distribution["percentages"].get(
                theme_name, 0
            )
            new_cache[theme_name]["vector_relevant_count"] = distribution[
                "counts"
            ].get(theme_name, 0)

        _theme_overview_cache[cache_key] = new_cache
        return jsonify(new_cache)

    except Exception as e:
        print(f"[DYNAMIC FILTER ERROR] {str(e)}")
        # Fallback to base cache if something goes wrong
        return jsonify(cache)


# ── VECTOR STATS ─────────────────────────────────────────────────────────────


@app.route("/api/vector-stats", methods=["GET"])
def vector_stats():
    """Get statistics and sample documents from vector DB"""
    try:
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))

        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify(
                {
                    "status": "empty",
                    "data": [],
                    "total_documents": 0,
                    "message": "Vector DB not initialized",
                }
            ), 200

        count = collection.count()

        if count == 0:
            return jsonify({"status": "empty", "data": [], "total_documents": 0}), 200

        # Get sample documents
        all_docs = collection.get(limit=min(count, 50))

        documents = []
        if all_docs["documents"]:
            for i, doc in enumerate(all_docs["documents"][:50]):
                documents.append(
                    {
                        "id": i + 1,
                        "text": doc[:200] + "..." if len(doc) > 200 else doc,
                        "full_text": doc,
                        "metadata": all_docs["metadatas"][i]
                        if all_docs["metadatas"]
                        else {},
                    }
                )

        return jsonify(
            {
                "status": "success",
                "data": documents,
                "total_documents": count,
                "samples": len(documents),
            }
        ), 200

    except Exception as e:
        print(f"[VECTOR STATS ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)
