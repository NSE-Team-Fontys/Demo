from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from vector_builder import build_vector_db
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path

# Import the process_file function from the script we made earlier
from anonymizer import process_file

app = Flask(__name__)
# Enable CORS so your React app (localhost:5173) can talk to this API (localhost:5000)
CORS(app)

UPLOAD_FILE = "temp_upload.csv"
OUTPUT_FILE = "anonymized_output.csv"
VECTOR_DB_PATH = Path('./survey_vector_db')

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
    data = request.json
    selected_columns = data.get('selected_columns', [])
    
    if not os.path.exists(UPLOAD_FILE):
        return jsonify({'status': 'error', 'error': 'File not found. Please upload again.'})
        
    try:
        # Call the standalone script to process the file
        process_file(
            input_path=UPLOAD_FILE, 
            output_path=OUTPUT_FILE, 
            columns_to_anonymize=selected_columns,
            sep=';'
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully saved to {OUTPUT_FILE}',
            'columns_anonymized': selected_columns
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})


@app.route('/api/build-vectordb', methods=['POST'])
def build_db():
    try:
        # Calls the function we just made, using the anonymized file
        result = build_vector_db(csv_path=OUTPUT_FILE)
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

@app.route('/api/status', methods=['GET'])
def status():
    anonymized_exists = os.path.exists(OUTPUT_FILE)
    vector_db_exists = os.path.exists('survey_vector_db') and any(os.scandir('survey_vector_db'))
    return jsonify({
        'status': 'success',
        'anonymized_exists': anonymized_exists,
        'vector_db_exists': vector_db_exists
    })

# ── QUERY VECTORS ────────────────────────────────────────────────────────────

@app.route('/api/query-vectors', methods=['GET'])
def query_vectors():
    """Search vectors with metadata filtering"""
    try:
        query_text = request.args.get('query', '').strip()
        top_k = min(int(request.args.get('n', 10)), 50)
        institution = request.args.get('institution', None)
        
        if not query_text:
            return jsonify({"status": "error", "error": "Empty query"}), 400
        
        print(f"[QUERY] Searching: '{query_text}' | Institution: {institution or 'all'} | Top-K: {top_k}")
        
        # Connect to vector DB
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        
        try:
            collection = client.get_collection("survey_responses")
        except:
            return jsonify({"status": "error", "error": "Vector database not found. Build vectors first."}), 400
        
        # Encode query
        model = SentenceTransformer('BAAI/bge-m3')
        query_embedding = model.encode(query_text, normalize_embeddings=True)
        
        # Build where filter
        where_filter = None
        if institution and institution != 'all':
            where_filter = {"institution": institution}
        
        # Query collection
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
            "query": query_text
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