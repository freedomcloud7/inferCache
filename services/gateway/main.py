"""
InferCache Gateway Service
FastAPI app that routes LLM requests through LiteLLM with KV cache optimization.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from services.cache.manager import CacheManager
from services.compression.obcache import OBCompressor
from services.metrics.exporter import MetricsCollector


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Settings:
    """Environment-driven configuration."""

    LITELLM_URL: str = os.getenv("LITELLM_URL", "http://localhost:4000")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET: str = os.getenv("MINIO_BUCKET", "infercache-cold")
    CACHE_TTL_HOT: int = int(os.getenv("CACHE_TTL_HOT", "300"))
    COMPRESSION_RATIO: int = int(os.getenv("COMPRESSION_RATIO", "10"))
    GATEWAY_PORT: int = int(os.getenv("GATEWAY_PORT", "8080"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/infercache")
    UPSTREAM_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")


settings = Settings()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    messages: list[dict[str, str]] = Field(..., description="Chat messages")
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False


class CacheStats(BaseModel):
    hit_rate: float
    memory_saved_mb: float
    active_sessions: int
    cost_savings_usd: float


# ---------------------------------------------------------------------------
# Application state
# ---------------------------------------------------------------------------

class AppState:
    def __init__(self) -> None:
        self.cache: CacheManager | None = None
        self.compressor: OBCompressor | None = None
        self.metrics: MetricsCollector | None = None
        self.http_client: httpx.AsyncClient | None = None

    async def init(self) -> None:
        try:
            self.cache = CacheManager(
                redis_url=settings.REDIS_URL,
                minio_endpoint=settings.MINIO_ENDPOINT,
                minio_access_key=settings.MINIO_ACCESS_KEY,
                minio_secret_key=settings.MINIO_SECRET_KEY,
                minio_bucket=settings.MINIO_BUCKET,
                ttl=settings.CACHE_TTL_HOT,
            )
            await self.cache.connect()
        except Exception as exc:
            logger.warning("Cache init failed: %s — running without cache", exc)
            self.cache = None

        self.compressor = OBCompressor(ratio=settings.COMPRESSION_RATIO)
        self.metrics = MetricsCollector()
        self.http_client = httpx.AsyncClient(timeout=120.0)

    async def shutdown(self) -> None:
        if self.cache:
            await self.cache.disconnect()
        if self.http_client:
            await self.http_client.aclose()


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await state.init()
    yield
    await state.shutdown()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="InferCache Gateway",
    description="KV-cache-optimized LLM routing gateway",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Cache key helpers
# ---------------------------------------------------------------------------

def _cache_key(model: str, messages: list[dict[str, str]]) -> str:
    canonical = json.dumps({"model": model, "messages": messages}, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "infercache-gateway"}


@app.get("/metrics")
async def metrics() -> StreamingResponse:
    """Prometheus exposition endpoint."""
    if not state.metrics:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    output = state.metrics.to_prometheus()
    return StreamingResponse(
        iter([output]),
        media_type="text/plain; version=0.0.4",
    )


@app.get("/stats", response_model=CacheStats)
async def stats() -> CacheStats:
    if not state.metrics:
        raise HTTPException(status_code=503, detail="Metrics not initialized")
    return CacheStats(
        hit_rate=state.metrics.hit_rate,
        memory_saved_mb=state.metrics.memory_saved_mb,
        active_sessions=state.metrics.active_sessions,
        cost_savings_usd=state.metrics.cost_savings,
    )


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> Any:
    if not all([state.compressor, state.metrics]):
        raise HTTPException(status_code=503, detail="Service initializing")

    # Try cache lookup if cache is available
    if state.cache is not None:
        key = _cache_key(request.model, request.messages)
        cached = await state.cache.get(key)
        if cached is not None:
            state.metrics.record_hit(len(str(request.messages)))
            if request.stream:
                return _stream_cached(cached)
            return JSONResponse(content=cached)
        state.metrics.record_miss()
    else:
        state.metrics.record_miss()

    # Forward to LiteLLM
    # Build headers — inject upstream API key if configured
    headers = {"Content-Type": "application/json"}
    if settings.UPSTREAM_API_KEY:
        # Anthropic uses x-api-key, not Authorization: Bearer
        headers["x-api-key"] = settings.UPSTREAM_API_KEY
        headers["anthropic-version"] = "2023-06-01"

    try:
        response = await state.http_client.post(
            f"{settings.LITELLM_URL}/v1/chat/completions",
            json=request.model_dump(),
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream error: {exc}")

    compressed = state.compressor.compress_kv(payload)
    if state.cache is not None:
        key = _cache_key(request.model, request.messages)
        await state.cache.set(key, payload, compressed)

    tokens_out = payload.get("usage", {}).get("total_tokens", 0)
    state.metrics.record_tokens(tokens_out)

    if request.stream:
        return _stream_response(payload)
    return JSONResponse(content=payload)


# ---------------------------------------------------------------------------
# Streaming helpers
# ---------------------------------------------------------------------------

def _stream_cached(data: dict[str, Any]) -> StreamingResponse:
    async def gen() -> AsyncIterator[bytes]:
        yield f"data: {json.dumps(data)}\n\n".encode()
        yield b"data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


async def _stream_response(data: dict[str, Any]) -> StreamingResponse:
    async def gen() -> AsyncIterator[bytes]:
        yield f"data: {json.dumps(data)}\n\n".encode()
        yield b"data: [DONE]\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT") or os.getenv("GATEWAY_PORT") or "8080")
    uvicorn.run("services.gateway.main:app", host="0.0.0.0", port=port)
