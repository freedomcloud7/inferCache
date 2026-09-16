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
    """Proxy chat completions to local Ollama."""
    
    # Build Ollama request
    body = {
        "model": request.model,
        "messages": request.messages,
        "stream": False,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens,
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")

    # Convert Ollama response to OpenAI format
    ollama_message = data.get("message", {})
    content = ollama_message.get("content", "")
    
    prompt_eval_count = data.get("prompt_eval_count", 0)
    eval_count = data.get("eval_count", 0)
    
    return JSONResponse(content={
        "id": f"chatcmpl-{os.urandom(8).hex()}",
        "object": "chat.completion",
        "created": int(__import__("time").time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content,
            },
            "finish_reason": "stop" if data.get("done", True) else "length",
        }],
        "usage": {
            "prompt_tokens": prompt_eval_count,
            "completion_tokens": eval_count,
            "total_tokens": prompt_eval_count + eval_count,
        },
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT") or "8080")
    uvicorn.run(app, host="0.0.0.0", port=port)
