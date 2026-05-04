import sys
try:
    from transformers import pipeline
    print("Transformers imported.")
except ImportError:
    print("Transformers not installed.")
    sys.exit(1)
