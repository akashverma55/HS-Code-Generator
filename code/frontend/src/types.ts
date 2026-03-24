export interface PredictRequest{
    description : string;
}

export interface Candidate{
    hscode: string;
    description: string;
    section: string;
    parent: string;
    score: number;
}

export interface PredictResponse{
    hscode:string;
    description: string;
    reason: string;
    candidates: Candidate[];
    latency: number;
}

export interface HealthResponse{
    status: string;
    indexed: number;
    llm: string;
}