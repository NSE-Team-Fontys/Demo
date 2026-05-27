import chromadb

from src.core.embedding_models import (
    DEFAULT_EMBEDDING_MODEL,
    describe_embedding_runtime,
    load_embedding_model,
)

# ── Config ────────────────────────────────────────────────────────────────────

DB_PATH         = './survey_vector_db'
COLLECTION      = 'survey_responses'
EMBEDDING_MODEL = DEFAULT_EMBEDDING_MODEL

DEFAULT_N_RESULTS   = 10
DEFAULT_INSTITUTION = None   # None = search across all institutions

# ── Connect ───────────────────────────────────────────────────────────────────

print("Connecting to database...")
client     = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_collection(COLLECTION)
total      = collection.count()
print(f"  {total} responses loaded")

print("\nLoading embedding model...")
collection_metadata = getattr(collection, "metadata", None) or {}
EMBEDDING_MODEL = collection_metadata.get("embedding_model") or EMBEDDING_MODEL
print(f"  Model: {EMBEDDING_MODEL}")
print(f"  Runtime: {describe_embedding_runtime(EMBEDDING_MODEL)}")
model = load_embedding_model(EMBEDDING_MODEL)
print("  Ready\n")

# ── Helper ────────────────────────────────────────────────────────────────────

def search(query: str, institution: str = None, n: int = DEFAULT_N_RESULTS):
    """
    Search the vector database.

    Args:
        query:       Natural language question or keyword
        institution: Filter to a specific institution ID (string), or None for all
        n:           Number of results to return
    """
    vector = model.encode(query, normalize_embeddings=True).tolist()

    where = {"institution": institution} if institution else None

    results = collection.query(
        query_embeddings=[vector],
        n_results=n,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    docs      = results["documents"][0]
    metas     = results["metadatas"][0]
    distances = results["distances"][0]

    print(f"\n── Results for: \"{query}\"" + (f"  [institution: {institution}]" if institution else "  [all institutions]"))
    print(f"   Showing top {len(docs)} of {total} responses\n")

    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        similarity = 1 - dist   # cosine distance → similarity score
        inst       = meta.get("institution", "?")
        print(f"  {i:>2}. [{inst}] (score: {similarity:.2f})")
        print(f"      {doc}\n")

    return docs, metas

# ── Interactive loop ──────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("Survey Vector DB — Query Interface")
    print("=" * 60)
    print("Commands:")
    print("  Just type a question    → search all institutions")
    print("  /inst 1                 → set institution filter to '1'")
    print("  /inst all               → remove institution filter")
    print("  /n 20                   → change number of results")
    print("  /status                 → show current settings")
    print("  /quit                   → exit")
    print("=" * 60 + "\n")

    current_institution = DEFAULT_INSTITUTION
    current_n           = DEFAULT_N_RESULTS

    while True:
        try:
            raw = input("Query > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        # Commands
        if raw.startswith("/inst "):
            val = raw[6:].strip()
            if val.lower() == "all":
                current_institution = None
                print(f"  Institution filter cleared — searching all")
            else:
                current_institution = val
                print(f"  Institution filter set to: {val}")
            continue

        if raw.startswith("/n "):
            try:
                current_n = int(raw[3:].strip())
                print(f"  Results per query set to: {current_n}")
            except ValueError:
                print("  Invalid number")
            continue

        if raw == "/status":
            inst_str = current_institution if current_institution else "all"
            print(f"  Institution: {inst_str}  |  Results: {current_n}")
            continue

        if raw in ("/quit", "/exit", "quit", "exit"):
            print("Exiting.")
            break

        # Search
        search(raw, institution=current_institution, n=current_n)


if __name__ == "__main__":
    main()
