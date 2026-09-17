"""InferCache Gateway - local Ollama edition."""
from __future__ import annotations

import os
import json
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

@app.get("/")
async def root() -> dict:
    return {
        "service": "infercache-gateway",
        "status": "running",
        "ollama_url": OLLAMA_URL,
        "docs": "/health, /v1/chat/completions",
    }

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "infercache-gateway"}

class ChatRequest(BaseModel):
    model: str = "llama3.2:1b"
    messages: list[dict[str, str]]
    max_tokens: int = 4096
    temperature: float = 0.7
    stream: bool = False

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> Any:
    """Proxy chat completions to local Ollama using OpenAI-compatible API."""
    
    # Build OpenAI-formatted request for Ollama's v1 endpoint
    body = {
        "model": request.model,
        "messages": request.messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "stream": request.stream,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/v1/chat/completions",
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")

    return JSONResponse(content=data)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT") or "8080")
    uvicorn.run(app, host="0.0.0.0", port=port)