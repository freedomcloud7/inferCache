"""InferCache Gateway entry point for local development with Ollama."""
from services.gateway.main import app, settings
from services.cache.manager import CacheManager
from services.compression.obcache import OBCompressor
from services.metrics.exporter import MetricsCollector
import os
import httpx

# Override settings for local Ollama
os.environ["LITELLM_URL"] = "http://localhost:11434"
os.environ["REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")

settings.LITELLM_URL = "http://localhost:11434"
settings.UPSTREAM_API_KEY = ""

async def init_state():
    """Initialize gateway state for local development."""
    from services.gateway.main import state
    try:
        state.cache = CacheManager(
            redis_url=settings.REDIS_URL,
            minio_endpoint="localhost:9000",
            minio_access_key="minioadmin",
            minio_secret_key="minioadmin",
            minio_bucket="infercache-cold",
            ttl=300,
        )
        await state.cache.connect()
    except Exception as e:
        print(f"Cache init failed: {e} — running without cache")
        state.cache = None

    state.compressor = OBCompressor(ratio=10)
    state.metrics = MetricsCollector()
    state.http_client = httpx.AsyncClient(timeout=120.0)

# Patch the lifespan to use local init
import asyncio
loop = asyncio.get_event_loop()
loop.run_until_complete(init_state())

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT") or os.getenv("GATEWAY_PORT") or "8080")
    uvicorn.run(app, host="0.0.0.0", port=port)
