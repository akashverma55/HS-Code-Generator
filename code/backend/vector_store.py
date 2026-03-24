from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document


# FAISS index saved to output/ folder at project root
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "langchain_faiss"

# Qwen3-Embedding — fully local, no API key
embeddings_model = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen3-Embedding-0.6B",
    model_kwargs={"trust_remote_code": True, "device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)

vector_db: FAISS | None = None


def build(rows: list[dict]) -> None:
    """Embed descriptions → build FAISS index → save to output/."""
    global vector_db
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    docs = [
        Document(
            page_content=row["text"],  
            metadata={
                "hscode":  row["hscode"],
                "parent":  row["parent"],
                "section": row["section"],
                "level":   row["level"],
            },
        )
        for row in rows
    ]

    vector_db = FAISS.from_documents(docs, embeddings_model)
    vector_db.save_local(str(OUTPUT_DIR))
    print(f"✅ FAISS index saved to output/ — {len(docs)} HS codes indexed")


def load() -> bool:
    """Load FAISS index from output/ into memory."""
    global vector_db
    if not OUTPUT_DIR.exists():
        return False
    vector_db = FAISS.load_local(
        str(OUTPUT_DIR),
        embeddings_model,
        allow_dangerous_deserialization=True,
    )
    print("✅ FAISS index loaded from output/")
    return True


def search(query: str, top_k: int = 10) -> list[dict]:
    """Pass plain-English description — Qwen3 embeds it, FAISS finds top matches."""
    if vector_db is None:
        return []
    results = vector_db.similarity_search_with_score(query, k=top_k)
    return [
        {
            "description": doc.page_content,
            "hscode":      doc.metadata["hscode"],
            "parent":      doc.metadata["parent"],
            "section":     doc.metadata["section"],
            "level":       doc.metadata["level"],
            "score":       float(score),
        }
        for doc, score in results
    ]


def count() -> int:
    return vector_db.index.ntotal if vector_db else 0