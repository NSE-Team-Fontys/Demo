import pandas as pd
from presidio_analyzer import AnalyzerEngine
from transformers import pipeline

def process_file(input_path: str, output_path: str, columns_to_anonymize: list, sep: str = ';'):
    df = pd.read_csv(input_path, sep=sep)
    
    # 1. Initialize Layer 1 (Presidio)
    print("Loading Layer 1 (Presidio)...")
    analyzer = AnalyzerEngine()
    
    # 2. Initialize Layer 2 (Transformer)
    print("Loading Layer 2 (EU-PII-Safeguard)...")
    hf_pipeline = pipeline(
        "token-classification", 
        model="tabularisai/eu-pii-safeguard", 
        aggregation_strategy="simple"
    )

    def mask_text(text):
        if pd.isna(text) or not isinstance(text, str) or not text.strip():
            return text
            
        spans = []
        
        # Run Layer 1
        l1_results = analyzer.analyze(text=text, language='en')
        for res in l1_results:
            spans.append((res.start, res.end))
            
        # Run Layer 2
        l2_results = hf_pipeline(text)
        for res in l2_results:
            spans.append((res['start'], res['end']))
            
        # Resolve overlaps (longest span wins)
        spans = sorted(spans, key=lambda s: s[1] - s[0], reverse=True)
        selected_spans = []
        for start, end in spans:
            if not any(start < se and end > ss for ss, se in selected_spans):
                selected_spans.append((start, end))
                
        # Apply masks right-to-left to prevent index shifting
        selected_spans.sort(key=lambda s: s[0], reverse=True)
        result = text
        for start, end in selected_spans:
            result = result[:start] + "[]" + result[end:]
            
        return result

    # Process specified columns
    for col in columns_to_anonymize:
        if col in df.columns:
            print(f"Anonymizing column: {col}...")
            df[col] = df[col].apply(mask_text)
        else:
            print(f"Column '{col}' not found.")

    # Export
    df.to_csv(output_path, sep=sep, index=False)
    print(f"Success. Saved to {output_path}")

if __name__ == "__main__":
    INPUT_FILE = "data.csv"
    OUTPUT_FILE = "data_clean.csv"
    TARGET_COLUMNS = ["feedback_text", "open_comments"]
    
    process_file(INPUT_FILE, OUTPUT_FILE, TARGET_COLUMNS)