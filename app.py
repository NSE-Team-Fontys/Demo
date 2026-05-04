from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
import os
from vector_builder import build_vector_db_stream
from anonymizer import process_file_with_layers
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
# Enable CORS so your React app (localhost:5173) can talk to this API (localhost:5000)
CORS(app)

UPLOAD_FILE = "temp_upload.csv"
OUTPUT_FILE = "anonymized_output.csv"
VECTOR_DB_PATH = Path('./survey_vector_db')
TEMP_DIR = Path('./temp')
ANONYMIZED_CSV_PATH = Path('./anonymized_survey.csv')

@app.route('/api/inspect-file', methods=['POST'])
def inspect_file():
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'error': 'No file uploaded'})
    
    # Save the file temporarily
    file.save(UPLOAD_FILE)
    
    try:
        # Read just the first few rows to get columns and a preview
        df = pd.read_csv(UPLOAD_FILE, sep=';', nrows=5)
        
        return jsonify({
            'status': 'success',
            'columns': df.columns.tolist(),
            'preview': df.head(1).to_dict(orient='records')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/anonymize', methods=['POST'])
def anonymize():
    """Anonymize uploaded file with selected layers"""
    try:
        data = request.json
        selected_columns = data.get('selected_columns', [])
        selected_layers = data.get('selected_layers', ['presidio', 'eu-pii'])
        
        input_file = Path(UPLOAD_FILE)
        output_file = ANONYMIZED_CSV_PATH
        
        if not input_file.exists():
            return jsonify({"status": "error", "error": "No file uploaded"}), 400
        
        print(f"[ANONYMIZE] Columns: {selected_columns} | Layers: {selected_layers}")
        
        return Response(
            process_file_with_layers(
                str(input_file),
                str(output_file),
                selected_columns,
                selected_layers
            ),
            mimetype='application/x-ndjson'
        )
        
    except Exception as e:
        print(f"[ANONYMIZE ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/build-vectors', methods=['POST'])
def build_vectors():
    """Build vector database with proper metadata storage"""
    try:
        if not ANONYMIZED_CSV_PATH.exists():
            return jsonify({"status": "error", "error": "Anonymized CSV not found"}), 400
        
        print("[BUILD-VECTORS] Starting vector DB build...")
        
        return Response(
            build_vector_db_stream(
                csv_path=str(ANONYMIZED_CSV_PATH),
                db_path=str(VECTOR_DB_PATH)
            ),
            mimetype='application/x-ndjson'
        )
        
    except Exception as e:
        print(f"[BUILD-VECTORS ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500




@app.route('/api/status', methods=['GET'])
def status():
    anonymized_exists = os.path.exists(ANONYMIZED_CSV_PATH)
    vector_db_exists = os.path.exists('survey_vector_db') and any(os.scandir('survey_vector_db'))
    return jsonify({
        'status': 'success',
        'anonymized_exists': anonymized_exists,
        'vector_db_exists': vector_db_exists
    })

# ── QUERY VECTORS ────────────────────────────────────────────────────────────

@app.route('/api/filter-options', methods=['GET'])
def get_filter_options():
    """Get available filter options from the vector database metadata"""
    try:
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        
        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify({
                "status": "empty",
                "options": {}
            }), 200
        
        # Get all documents with metadata
        all_docs = collection.get(limit=collection.count())
        
        # Extract unique values from metadata
        institutions = set()
        years = set()
        locations = set()
        programmes = set()
        study_modes = set()
        cohorts = set()
        
        if all_docs['metadatas']:
            for meta in all_docs['metadatas']:
                if meta.get('institution'):
                    institutions.add(str(meta['institution']))
                if meta.get('academic_year'):
                    years.add(str(meta['academic_year']))
                if meta.get('location'):
                    locations.add(str(meta['location']))
                if meta.get('programme'):
                    programmes.add(str(meta['programme']))
                if meta.get('study_mode'):
                    study_modes.add(str(meta['study_mode']))
                if meta.get('cohort'):
                    cohorts.add(str(meta['cohort']))
        
        return jsonify({
            "status": "success",
            "options": {
                "institutions": sorted(list(institutions)),
                "academic_years": sorted(list(years)),
                "locations": sorted(list(locations)),
                "programmes": sorted(list(programmes)),
                "study_modes": sorted(list(study_modes)),
                "cohorts": sorted(list(cohorts))
            }
        })
        
    except Exception as e:
        print(f"[FILTER OPTIONS ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route('/api/query-vectors', methods=['GET'])
def query_vectors():
    """Search vectors with metadata filtering"""
    try:
        query_text = request.args.get('query', '').strip()
        top_k = min(int(request.args.get('n', 10)), 50)
        
        if not query_text:
            return jsonify({"status": "error", "error": "Empty query"}), 400
        
        # Get filters from query params
        filters = {}
        if request.args.get('institution') and request.args.get('institution') != 'all':
            filters['institution'] = request.args.get('institution')
        if request.args.get('academic_year') and request.args.get('academic_year') != 'all':
            filters['academic_year'] = request.args.get('academic_year')
        if request.args.get('location') and request.args.get('location') != 'all':
            filters['location'] = request.args.get('location')
        if request.args.get('programme') and request.args.get('programme') != 'all':
            filters['programme'] = request.args.get('programme')
        if request.args.get('study_mode') and request.args.get('study_mode') != 'all':
            filters['study_mode'] = request.args.get('study_mode')
        if request.args.get('cohort') and request.args.get('cohort') != 'all':
            filters['cohort'] = request.args.get('cohort')
        
        print(f"[QUERY] Searching: '{query_text}' | Filters: {filters}")
        
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        
        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify({"status": "error", "error": "Vector database not found. Build vectors first."}), 400
        
        model = SentenceTransformer('BAAI/bge-m3')
        query_embedding = model.encode(query_text, normalize_embeddings=True)
        
        # Build where filter - support multiple conditions
        where_filter = None
        if filters:
            conditions = [{key: value} for key, value in filters.items()]
            if len(conditions) > 1:
                where_filter = {"$and": conditions}
            else:
                where_filter = conditions[0]
        
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i]
                similarity = max(0, 1 - distance)
                
                result_item = {
                    "id": i + 1,
                    "document": doc,
                    "preview": doc[:300] + "..." if len(doc) > 300 else doc,
                    "similarity": round(similarity, 3),
                    "percentage": round(similarity * 100, 1)
                }
                
                if results['metadatas'] and i < len(results['metadatas'][0]):
                    result_item["metadata"] = results['metadatas'][0][i]
                
                formatted.append(result_item)
        
        return jsonify({
            "status": "success",
            "results": formatted,
            "count": len(formatted),
            "query": query_text,
            "filters_applied": filters
        })
        
    except Exception as e:
        print(f"[QUERY ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


# ── VECTOR STATS ─────────────────────────────────────────────────────────────

@app.route('/api/vector-stats', methods=['GET'])
def vector_stats():
    """Get statistics and sample documents from vector DB"""
    try:
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        
        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify({
                "status": "empty",
                "data": [],
                "total_documents": 0,
                "message": "Vector DB not initialized"
            }), 200
        
        count = collection.count()
        
        if count == 0:
            return jsonify({
                "status": "empty",
                "data": [],
                "total_documents": 0
            }), 200
        
        # Get sample documents
        all_docs = collection.get(limit=min(count, 50))
        
        documents = []
        if all_docs['documents']:
            for i, doc in enumerate(all_docs['documents'][:50]):
                documents.append({
                    "id": i + 1,
                    "text": doc[:200] + "..." if len(doc) > 200 else doc,
                    "full_text": doc,
                    "metadata": all_docs['metadatas'][i] if all_docs['metadatas'] else {}
                })
        
        return jsonify({
            "status": "success",
            "data": documents,
            "total_documents": count,
            "samples": len(documents)
        }), 200
        
    except Exception as e:
        print(f"[VECTOR STATS ERROR] {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)