from importlib import import_module

from flask import Blueprint, Response, jsonify, request

anonymize_bp = Blueprint("anonymize", __name__)
service = import_module("src.pipeline.anonymization.service")


@anonymize_bp.route("/api/inspect-file", methods=["POST"])
def inspect_file():
    try:
        return jsonify(service.inspect_uploaded_file(request.files.get("file")))
    except ValueError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@anonymize_bp.route("/api/anonymize", methods=["POST"])
def anonymize():
    try:
        data = request.get_json(silent=True) or {}
        stream = service.anonymize_uploaded_file(
            data.get("selected_columns", []),
            data.get("selected_layers", ["presidio", "eu-pii"]),
        )
        return Response(stream, mimetype="application/x-ndjson")
    except FileNotFoundError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except Exception as exc:
        print(f"[ANONYMIZE ERROR] {str(exc)}")
        return jsonify({"status": "error", "error": str(exc)}), 500


@anonymize_bp.route("/api/inspect-anonymized", methods=["GET"])
def inspect_anonymized():
    try:
        return jsonify(service.inspect_anonymized_file())
    except FileNotFoundError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@anonymize_bp.route("/api/run-anonymize-check", methods=["POST"])
def run_anonymize_check():
    try:
        return Response(
            service.run_anonymize_check_stream(),
            mimetype="application/x-ndjson",
        )
    except FileNotFoundError as exc:
        return jsonify({"status": "error", "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@anonymize_bp.route("/api/anonymize-report", methods=["GET"])
def anonymize_report():
    return jsonify(service.anonymize_report_payload())


@anonymize_bp.route("/api/checkpoint-status", methods=["GET"])
def checkpoint_status():
    return jsonify(service.checkpoint_status_payload())
