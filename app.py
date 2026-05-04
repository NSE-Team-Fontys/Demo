from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from vector_builder import build_vector_db

# Import the process_file function from the script we made earlier
from anonymizer import process_file

app = Flask(__name__)
# Enable CORS so your React app (localhost:5173) can talk to this API (localhost:5000)
CORS(app)

UPLOAD_FILE = "temp_upload.csv"
OUTPUT_FILE = "anonymized_output.csv"

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

if __name__ == '__main__':
    app.run(port=5000, debug=True)