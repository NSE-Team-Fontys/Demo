import pandas as pd
from presidio_analyzer import AnalyzerEngine
from transformers import pipeline

import json
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def process_file_with_layers(input_path: str, output_path: str, columns_to_anonymize: list, layers: list, sep: str = ';'):
    df = pd.read_csv(input_path, sep=sep)
    
    yield json.dumps({"status": "progress", "message": "Initializing...", "progress": 5}) + "\n"
    
    analyzer = None
    hf_pipeline = None
    
    if 'presidio' in layers:
        yield json.dumps({"status": "progress", "message": "Loading Layer 1 (Presidio)...", "progress": 10}) + "\n"
        analyzer = AnalyzerEngine()
    
    if 'eu-pii' in layers:
        yield json.dumps({"status": "progress", "message": "Loading Layer 2 (EU-PII-Safeguard)...", "progress": 20}) + "\n"
        hf_pipeline = pipeline(
            "token-classification", 
            model="tabularisai/eu-pii-safeguard", 
            aggregation_strategy="simple"
        )

    def mask_text(text):
        if pd.isna(text) or not isinstance(text, str) or not text.strip():
            return text
            
        spans = []
        
        if analyzer:
            l1_results = analyzer.analyze(text=text, language='en')
            for res in l1_results:
                spans.append((res.start, res.end))
        
        if hf_pipeline:
            l2_results = hf_pipeline(text)
            for res in l2_results:
                spans.append((res['start'], res['end']))
        
        if not spans:
            return text
        
        spans = sorted(spans, key=lambda s: s[1] - s[0], reverse=True)
        selected_spans = []
        for start, end in spans:
            if not any(start < se and end > ss for ss, se in selected_spans):
                selected_spans.append((start, end))
        
        selected_spans.sort(key=lambda s: s[0], reverse=True)
        result = text
        for start, end in selected_spans:
            result = result[:start] + "[]" + result[end:]
        
        return result

    total_cols = len(columns_to_anonymize)
    total_rows = len(df)
    
    for col_idx, col in enumerate(columns_to_anonymize):
        if col in df.columns:
            yield json.dumps({"status": "progress", "message": f"Anonymizing column: {col}...", "progress": 20 + int(70 * (col_idx / total_cols))}) + "\n"
            
            for i in range(total_rows):
                text = df.at[i, col]
                df.at[i, col] = mask_text(text)
                
                # Yield progress updates every row or so, to give real-time feedback
                base_progress = 20 + int(70 * (col_idx / total_cols))
                row_progress = int((70 / total_cols) * ((i + 1) / total_rows))
                yield json.dumps({
                    "status": "progress",
                    "column": col,
                    "row": i + 1,
                    "total_rows": total_rows,
                    "preview": str(text)[:60] + "..." if pd.notna(text) else "",
                    "progress": base_progress + row_progress,
                    "message": f"Processing row {i + 1}/{total_rows} in {col}"
                }) + "\n"
        else:
            yield json.dumps({"status": "progress", "message": f"Column '{col}' not found.", "progress": 20}) + "\n"

    df.to_csv(output_path, sep=sep, index=False)
    yield json.dumps({"status": "success", "message": "Anonymization complete", "rows_processed": total_rows, "columns_anonymized": columns_to_anonymize, "progress": 100}) + "\n"

if __name__ == "__main__":
    INPUT_FILE = "data.csv"
    OUTPUT_FILE = "data_clean.csv"
    TARGET_COLUMNS = ["feedback_text", "open_comments"]
    
    process_file_with_layers(INPUT_FILE, OUTPUT_FILE, TARGET_COLUMNS, ['presidio', 'eu-pii'])