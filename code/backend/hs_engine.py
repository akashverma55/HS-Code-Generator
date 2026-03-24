import torch
from unsloth import FastLanguageModel
import re
import vector_store
from csv_loader import load_csv

# ── Config ────────────────────────────────────────────────────────────────────
LLM_MODEL      = "unsloth/llama-3.2-1b-Instruct-bnb-4bit"
max_seq_length = 4096
dtype          = None
load_in_4bit   = True

SYSTEM_PROMPT = (
    "You are an expert HS Code classifier for international trade. "
    "You will receive a product description and candidate HS codes. "
    "Pick the single most accurate HS code and respond in EXACTLY this format with nothing else:\n\n"
    "HS Code: 010121\n"
    "Description: Horses; live, pure-bred breeding animals\n"
    "Reason: This code matches because...\n\n"
    "Rules:\n"
    "- HS Code line must contain ONLY the numeric code, nothing else.\n"
    "- Do not add extra text, explanations, or formatting.\n"
    "- Follow the exact 3-line format shown above."
)

# ── Load LLM ──────────────────────────────────────────────────────────────────
print(f"Loading {LLM_MODEL}...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=LLM_MODEL,
    max_seq_length=max_seq_length,
    dtype=dtype,
    load_in_4bit=load_in_4bit,
)
FastLanguageModel.for_inference(model)
print("✅ LLM ready")


def build_index() -> int:
    rows = load_csv()
    if not rows:
        return 0
    vector_store.build(rows)
    return len(rows)


def predict(product_description: str) -> dict:
    """
    1. Search FAISS for top 5 candidate HS codes
    2. LLM picks best one and explains why
    3. Return structured result — nothing saved to disk
    """

    # Step 1 — retrieve candidates
    candidates = vector_store.search(product_description, top_k=10)

    if not candidates:
        return {
            "hscode":      "Not found",
            "description": "No HS codes indexed. Run: python scripts/ingest.py",
            "reason":      "",
            "candidates":  [],
        }

    # Step 2 — format candidates for LLM
    candidates_text = "\n".join(
        f"{i+1}. HS Code: {c['hscode']} | {c['description']} | Section: {c['section']} | Parent: {c['parent']}"
        for i, c in enumerate(candidates)
    )

    user_message = (
        f"Product: {product_description}\n\n"
        f"Candidates:\n{candidates_text}\n\n"
        f"Pick the best HS code."
    )

    # Step 3 — generate (no session, no history — just one-shot)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=256,
            use_cache=True,
            do_sample=False,
        )

    new_tokens = output_ids[0][inputs["input_ids"].shape[1]:]
    raw = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    print("=" * 50)
    print("LLM RAW OUTPUT:")
    print(raw)
    print("=" * 50)

    match = re.search(r"\d+", raw)
    predicted_code = match.group().strip() if match else ""

    # Find the matching candidate to get description
    matched = next((c for c in candidates if c["hscode"] == predicted_code), None)
    # Step 4 — parse LLM output
    return {
        "hscode":      predicted_code,
        "description": matched["description"] if matched else "",
        "reason":      f"This code was selected as the best match for '{product_description}' based on semantic similarity with the official HS rulebook.",
        "candidates":  candidates,
    }


def _parse(text: str, field: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.lower().startswith(field.lower() + ":"):
            value = line.split(":", 1)[1].strip()
            # For HS Code, extract only the numeric part
            if field.lower() == "hs code":
                import re
                match = re.search(r"\d+", value)
                return match.group() if match else value
            return value
    return ""