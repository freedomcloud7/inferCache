"""InferCache Gateway entry point for Railway deployment."""

import os
import time
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any

app = FastAPI(
    title="InferCache Gateway",
    description="KV-cache-optimized LLM routing gateway",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get API keys from environment (Railway will set these)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Map of model names to providers
MODEL_PROVIDERS = {
    "gpt-4": "openai",
    "gpt-3.5-turbo": "openai",
    "gpt-4-turbo": "openai",
    "claude-3-opus": "anthropic",
    "claude-3-sonnet": "anthropic",
    "claude-3-haiku": "anthropic",
    "gemini-pro": "google",
}


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
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "infercache-gateway"}


def get_provider(model: str) -> str:
    """Determine provider from model name."""
    model_lower = model.lower()
    for key, provider in MODEL_PROVIDERS.items():
        if key in model_lower or model_lower in key:
            return provider
    return "openai"


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> Any:
    """Route chat completions to upstream provider."""
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    provider = get_provider(request.model)
    
    # Build request body
    body = {
        "model": request.model,
        "messages": request.messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }
    
    if request.stream:
        body["stream"] = True
    
    # Route to appropriate provider
    if provider == "anthropic":
        api_key = ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY", "")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        url = "https://api.anthropic.com/v1/messages"
        response = await client_post(url, body, headers)
        data = await response.json()
        result = normalize_anthropic_response(data)
    elif provider == "google":
        api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        gemini_msg = messages_to_gemini_format(request.messages)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        body_gemini = {"contents": [gemini_msg], "generationConfig": {"temperature": request.temperature}}
        response = await client_post(url, body_gemini, {"Content-Type": "application/json"})
        data = await response.json()
        result = normalize_gemini_response(data)
    else:
        # Default to OpenAI
        api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = "https://api.openai.com/v1/chat/completions"
        response = await client_post(url, body, headers)
        result = await response.json()
    
    return JSONResponse(content=result)


async def client_post(url: str, body: dict, headers: dict) -> httpx.Response:
    """Make HTTP POST request with error handling."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=body, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Upstream error: {response.text}")
        return response


def normalize_anthropic_response(data: dict) -> dict:
    """Convert Anthropic response to OpenAI format."""
    content = ""
    if data.get("content"):
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
    
    return {
        "id": data.get("id", f"chatcmpl-{int(time.time())}"),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": data.get("model", "claude-unknown"),
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            "total_tokens": data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
        },
    }


def messages_to_gemini_format(messages: list) -> dict:
    """Convert OpenAI messages to Gemini format."""
    if not messages:
        return {}
    last = messages[-1]
    return {
        "role": last.get("role", "user"),
        "parts": [{"text": last.get("content", "")}]
    }


def normalize_gemini_response(data: dict) -> dict:
    """Convert Gemini response to OpenAI format."""
    content = ""
    candidates = data.get("candidates", [])
    if candidates:
        content_parts = candidates[0].get("content", {}).get("parts", [])
        for part in content_parts:
            content += part.get("text", "")
    
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "gemini-pro",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop",
        }],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        },
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)