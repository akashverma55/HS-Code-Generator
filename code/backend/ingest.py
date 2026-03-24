import sys
import time
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).parent))
 
from csv_loader import load_csv
import vector_store
 
if __name__ == "__main__":
    print("=" * 50)
    print("  HS Code Generator — FAISS Index Builder")
    print("=" * 50)
 
    # Step 1 — Load CSV
    print("\n[1/3] Reading CSV from input/hscodes.csv ...")
    rows = load_csv()
    if not rows:
        print("❌ No rows found. Make sure input/hscodes.csv exists.")
        sys.exit(1)
    print(f"✅ Loaded {len(rows)} HS code rows.")
 
    # Step 2 — Embed + Build index
    print("\n[2/3] Embedding descriptions with Qwen3 on CPU ...")
    print("      This may take a few minutes for 6000+ rows. Please wait...")
    print("      (embedding model is running on CPU — no GPU needed for this step)")
 
    t0 = time.perf_counter()
    vector_store.build(rows)
    elapsed = round(time.perf_counter() - t0, 1)
 
    # Step 3 — Done
    print(f"\n[3/3] Done! Index saved to output/langchain_faiss/")
    print(f"      Total time: {elapsed} seconds")
    print(f"      Total rows indexed: {len(rows)}")
    print("\n✅ You can now start the server:")
    print("      uvicorn main:app --port 8000")
    print("=" * 50)