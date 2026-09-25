"""InferCache Gateway - OpenRouter Edition for easy deployment with one key."""

import os
import time
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any


app = FastAPI(
    title="InferCache Gateway",
    description="KV-cache-optimized LLM routing via OpenRouter (single API key)",
    version="1.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "")
VALID_API_KEYS = set(k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip())


def verify_api_key(request: Request):
    if not VALID_API_KEYS:
        return
    key = request.headers.get("X-API-Key", "")
    if key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key. Provide X-API-Key header.")


class ChatRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    messages: list[dict[str, str]] = Field(..., description="Chat messages")
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": "infercache-gateway",
        "status": "running",
        "provider": "openrouter" if OPENROUTER_API_KEY else "local-ollama",
        "docs": "/health, /v1/chat/completions",
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "infercache-gateway"}


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, req: Request) -> Any:
    verify_api_key(req)
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    if OPENROUTER_API_KEY:
        return await chat_via_openrouter(request)
    if OLLAMA_URL:
        return await chat_via_ollama(request)
    raise HTTPException(status_code=502, detail="No API key or Ollama URL configured")


async def chat_via_openrouter(request: ChatRequest) -> Any:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://hermes-agent.nousresearch.com",
        "X-Title": "InferCache-Gateway",
    }
    body = {"model": request.model, "messages": request.messages, "max_tokens": request.max_tokens, "temperature": request.temperature}
    if request.stream:
        body["stream"] = True
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=body, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"OpenRouter error: {response.text}")
        return await response.json()


async def chat_via_ollama(request: ChatRequest) -> Any:
    headers = {"Content-Type": "application/json"}
    body = {"model": request.model, "messages": request.messages, "max_tokens": request.max_tokens, "temperature": request.temperature, "stream": False}
    src = OLLAMA_URL.rstrip("/")
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(src + "/v1/chat/completions", json=body, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Ollama error: {response.text}")
        return await response.json()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
