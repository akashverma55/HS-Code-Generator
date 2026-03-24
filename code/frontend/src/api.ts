import type { PredictResponse , HealthResponse } from "./types";

const BASE = "/api";

export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BASE}/health`);
  return res.json();
}

export async function predict(description: string): Promise<PredictResponse> {
    const res = await fetch(`${BASE}/predict`,{
        method: "POST",
        headers: {
            "Content-Type":"application/json"
        },
        body: JSON.stringify({description}),
    });
    if(!res.ok){
        const err = await res.json().catch(()=>({}));
        throw new Error(err.detail??`HTTP ${res.status}`);
    }
    return res.json();
}