from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import pandas as pd
import os
from vector_builder import build_vector_db_stream
from anonymizer import process_file_with_layers
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer
import json

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

CACHE_FILE = Path('./gemma_cache.json')

def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        import json
        json.dump(cache_data, f, indent=2)

@app.route('/api/theme-summary', methods=['POST'])
def theme_summary():
    try:
        data = request.json
        theme_name = data.get('theme', '')
        theme_query = data.get('query', '')
        
        if not theme_query:
            return jsonify({"status": "error", "error": "No query provided"}), 400
            
        print(f"[GEMMA4] Processing theme summary for: {theme_name}")
        
        cache = load_cache()
        if theme_name in cache:
            print(f"[GEMMA4] Returning cached summary for: {theme_name}")
            cached_data = cache[theme_name]
            cached_data["status"] = "success"
            return jsonify(cached_data)
        
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        collection = client.get_collection("survey_responses")
        
        model = SentenceTransformer('BAAI/bge-m3')
        query_embedding = model.encode(theme_query, normalize_embeddings=True)
        
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=20,
            include=["documents", "distances"]
        )
        
        # Filter for relevance > 0.6
        relevant_docs = []
        if results['documents'] and len(results['documents']) > 0:
            for i, doc in enumerate(results['documents'][0]):
                distance = results['distances'][0][i]
                similarity = max(0, 1 - distance)
                if similarity >= 0.5:
                    relevant_docs.append(doc)
                    
        # Real Gemma Call via Ollama
        import requests
        
        prompt = f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Also extract 3 to 5 short sub-themes or topics mentioned (e.g. "Lecture Pacing", "Teacher Availability").
Respond EXACTLY in this JSON format:
{{
  "summary": "...",
  "sentiments": [
    {{"sentiment": "Positive", "point": "..."}}
  ],
  "subthemes": ["...", "..."]
}}

Responses:
"""
        for doc in relevant_docs[:15]:
            prompt += f"- {doc}\n"
            
        real_quotes = relevant_docs[:3] if len(relevant_docs) >= 3 else relevant_docs
        
        try:
            print(f"[GEMMA] Sending {len(relevant_docs)} docs to local Ollama (gemma model)...")
            response = requests.post('http://localhost:11434/api/generate', json={
                "model": "gemma4:e4b",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=120)
            
            if response.status_code == 200:
                result_text = response.json().get('response', '{}')
                print(f"[GEMMA] Raw response received: {result_text}")
                
                import json
                import re
                
                # Attempt to extract a JSON block if wrapped in markdown
                match = re.search(r'\{[\s\S]*\}', result_text)
                json_str = match.group(0) if match else result_text
                
                try:
                    parsed = json.loads(json_str)
                except json.JSONDecodeError:
                    print("[GEMMA] Strict JSON parse failed. Raw string:", json_str)
                    raise Exception(f"Invalid JSON structure returned by model: {json_str[:150]}")
                    
                summary = parsed.get("summary", "Summary could not be parsed.")
                sentiments = parsed.get("sentiments", [])
                subthemes = parsed.get("subthemes", [])
            else:
                error_body = response.text
                raise Exception(f"Ollama returned status {response.status_code}: {error_body}")
                
        except requests.exceptions.ConnectionError:
            return jsonify({
                "status": "error", 
                "error": "Could not connect to Ollama. To use real AI generation, please ensure Ollama is installed and running locally with the 'gemma' model."
            }), 503
        except Exception as e:
            error_msg = str(e)
            print(f"[GEMMA ERROR] {error_msg}")
            
            # Extract raw text if it exists
            raw = locals().get('result_text', None)
            
            summary = f"Gemma encountered an error: {error_msg}"
            if raw:
                 summary += f" | Raw output: {raw[:150]}..."
                 
            sentiments = []
            subthemes = []
            real_quotes = []
            
        response_data = {
            "status": "success",
            "theme": theme_name,
            "document_count": len(relevant_docs),
            "summary": summary,
            "sentiments": sentiments,
            "subthemes": subthemes,
            "quotes": real_quotes
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

@app.route('/api/precompute-insights', methods=['POST'])
def precompute_insights():
    """Stream NDJSON progress as we precompute insights for all themes."""
    data = request.json
    themes = data.get('themes', [])
    
    if not themes:
        return jsonify({"error": "No themes provided"}), 400
        
    def generate():
        try:
            client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
            collection = client.get_collection("survey_responses")
            total_docs = collection.count()
            cache = load_cache()
            
            import requests, json, re
            
            for i, theme in enumerate(themes):
                theme_name = theme.get('name')
                query = theme.get('query', theme_name)
                
                yield json.dumps({
                    "status": "progress", 
                    "theme": theme_name, 
                    "progress": int((i / len(themes)) * 100),
                    "message": f"Querying VectorDB for {theme_name}..."
                }) + "\n"
                
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('BAAI/bge-m3')
                query_embedding = model.encode(query, normalize_embeddings=True)
                
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=min(total_docs, 50),
                    include=["documents", "distances"]
                )
                
                relevant_docs = []
                if results['documents'] and len(results['documents']) > 0:
                    for j, doc in enumerate(results['documents'][0]):
                        distance = results['distances'][0][j]
                        similarity = max(0, 1 - distance)
                        if similarity >= 0.5:
                            relevant_docs.append(doc)
                
                frequency = int((len(relevant_docs) / max(total_docs, 1)) * 100) if total_docs > 0 else 0
                
                # Check cache for summary
                if theme_name in cache and "summary" in cache[theme_name] and not "error" in cache[theme_name].get("summary", ""):
                    # Update frequency but keep summary
                    cache[theme_name]["frequency"] = frequency
                    save_cache(cache)
                    continue
                    
                yield json.dumps({
                    "status": "progress", 
                    "theme": theme_name, 
                    "progress": int(((i + 0.5) / len(themes)) * 100),
                    "message": f"Generating Gemma summary for {theme_name}..."
                }) + "\n"
                
                if not relevant_docs:
                    cache[theme_name] = {
                        "frequency": frequency,
                        "summary": "Not enough highly relevant responses found.",
                        "sentiments": []
                    }
                    save_cache(cache)
                    continue
                
                prompt = f"""You are an expert data analyst. Read the following student survey responses about '{theme_name}'.
Summarize the general consensus in 2 sentences. Extract 3 key sentiments (Positive, Neutral, or Critical) and provide a 1-sentence point for each.
Also extract 3 to 5 short sub-themes or topics mentioned.
Respond EXACTLY in this JSON format:
{{
  "summary": "...",
  "sentiments": [
    {{"sentiment": "Positive", "point": "..."}}
  ],
  "subthemes": ["...", "..."]
}}

Responses:
"""
                for doc in relevant_docs[:15]:
                    prompt += f"- {doc}\n"
                    
                real_quotes = relevant_docs[:3] if len(relevant_docs) >= 3 else relevant_docs
                    
                try:
                    response = requests.post('http://localhost:11434/api/generate', json={
                        "model": "gemma4:e4b", "prompt": prompt, "stream": False, "format": "json"
                    }, timeout=120)
                    
                    if response.status_code == 200:
                        result_text = response.json().get('response', '{}')
                        match = re.search(r'\{[\s\S]*\}', result_text)
                        json_str = match.group(0) if match else result_text
                        parsed = json.loads(json_str)
                        
                        cache[theme_name] = {
                            "frequency": frequency,
                            "summary": parsed.get("summary", "Summary could not be parsed."),
                            "sentiments": parsed.get("sentiments", []),
                            "subthemes": parsed.get("subthemes", []),
                            "quotes": real_quotes
                        }
                    else:
                        cache[theme_name] = {
                            "frequency": frequency,
                            "summary": f"Ollama Error: Status {response.status_code}",
                            "sentiments": [],
                            "subthemes": [],
                            "quotes": []
                        }
                except Exception as e:
                    cache[theme_name] = {
                        "frequency": frequency,
                        "summary": f"Failed to generate summary: {str(e)}",
                        "sentiments": [],
                        "subthemes": [],
                        "quotes": []
                    }
                save_cache(cache)
                
            yield json.dumps({"status": "success", "message": "All insights generated!", "progress": 100}) + "\n"
            
        except Exception as e:
            yield json.dumps({"status": "error", "message": str(e)}) + "\n"
            
    return Response(generate(), mimetype='application/x-ndjson')

@app.route('/api/themes-overview', methods=['GET'])
def get_themes_overview():
    cache = load_cache()
    
    # Check for filters
    filters = {}
    for key in ['institution', 'academic_year', 'location', 'programme', 'study_mode', 'cohort']:
        val = request.args.get(key)
        if val and val != 'All':
            filters[key] = val
            
    if not filters:
        return jsonify(cache)
        
    # We have filters, dynamically calculate frequencies
    try:
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        collection = client.get_collection("survey_responses")
        
        where_clause = {}
        if len(filters) == 1:
            k, v = list(filters.items())[0]
            where_clause = {k: v}
        elif len(filters) > 1:
            where_clause = {"$and": [{k: v} for k, v in filters.items()]}
            
        # Total matching documents
        filtered_docs = collection.get(where=where_clause)
        total_docs = len(filtered_docs['ids']) if filtered_docs and filtered_docs['ids'] else 0
        
        import copy
        new_cache = copy.deepcopy(cache)
        
        if total_docs == 0:
            for theme in new_cache:
                new_cache[theme]["frequency"] = 0
            return jsonify(new_cache)
            
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('BAAI/bge-m3')
        
        themes_list = ["Content and Organisation", "Professional Practice", "Teachers", "Support / Mentoring", "Examination & Assessment", "Engagement & Contact", "Special Circumstances"]
        
        for theme_name in themes_list:
            if theme_name not in new_cache: continue
            
            query_embedding = model.encode(theme_name, normalize_embeddings=True)
            results = collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=min(total_docs, 50),
                where=where_clause,
                include=["documents", "distances"]
            )
            
            relevant_docs = []
            if results['documents'] and len(results['documents']) > 0:
                for j, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][j]
                    similarity = max(0, 1 - distance)
                    if similarity >= 0.5:
                        relevant_docs.append(doc)
            
            new_cache[theme_name]["frequency"] = int((len(relevant_docs) / total_docs) * 100)
            
        return jsonify(new_cache)
        
    except Exception as e:
        print(f"[DYNAMIC FILTER ERROR] {str(e)}")
        # Fallback to base cache if something goes wrong
        return jsonify(cache)
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