import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).parent.parent.parent / "input" / "harmonized-system.csv"

def load_csv() -> list[dict]:
    if not CSV_PATH.exists():
        raise FileExistsError(f"CSV not found at: {CSV_PATH}")
    
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]


    rows = []
    for _, row in df.iterrows():
        description = row.get("description", "").strip()
        hscode      = row.get("hscode", "").strip()
        if not description or not hscode:
            continue
        rows.append({
            "text"      : description,
            "hscode"    : hscode,
            "parent"    : row.get("parent", "").strip(),
            "section"   : row.get("section", "").strip(),
            "level"     : row.get("level", "").strip(),
        })

    print(f"✅ Loaded {len(rows)} HS code rows from input/hscodes.csv")
    return rows
