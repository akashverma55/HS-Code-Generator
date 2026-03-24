import asyncio
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import vector_store
import hs_engine
# Run this once in a separate terminal
import torch
torch.cuda.empty_cache()
print(torch.cuda.memory_summary())

app = FastAPI(title='HS Code Generator', version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    loaded = vector_store.load()
    if not loaded:
        print("No index found. Building automatically from input/hscodes.csv ...")
        await asyncio.to_thread(hs_engine.build_index)
        print("✅ Index built and ready.")
    
class PredictRequest(BaseModel):
    description: str

class Candidate(BaseModel):
    hscode: str
    description: str
    section: str
    parent: str
    score: float

class PredictResponse(BaseModel):
    hscode: str
    description: str
    reason: str
    candidates: list[Candidate]
    latency: float

@app.get("/health")
def health():
    return {
        "status":  "ok",
        "indexed": vector_store.count(),
        "llm":     hs_engine.LLM_MODEL,
    }

@app.post("/predict", response_model = PredictResponse)
async def predict(req: PredictRequest):
    if not req.description.strip():
        raise HTTPException(400, "Description cannot be empty")
    
    timer = time.perf_counter()
    result = await asyncio.to_thread(hs_engine.predict, req.description)
    latency = round((time.perf_counter()-timer)*1000, 2)

    return PredictResponse(
        hscode = result["hscode"],
        description = result["description"],
        reason = result["reason"],
        candidates = [Candidate(**c) for c in result["candidates"]],
        latency = latency
    )