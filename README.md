# InferCache

**KV-cache-optimized LLM routing gateway** — deployable as a one-click Railway template.

InferCache sits between your application and LLM providers (OpenAI, Anthropic, Gemini) to slash costs via:

- **KV-cache compression** (OBCache-style, 10x+ reduction)
- **Two-tier caching** (Redis hot + MinIO cold)
- **Multi-provider routing** via LiteLLM
- **Grafana observability** out of the box

---

## Quick Start

### Local Development

```bash
# Clone
git clone https://github.com/infercache/infercache.git
cd infercache

# Set API keys
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=AIza...

# Start all services
cd infrastructure/docker
docker compose up --build
```

Services:
| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8080 | Main API (InferCache) |
| LiteLLM | 4000 | Multi-provider proxy |
| Redis | 6379 | Hot cache tier |
| MinIO | 9000 | Cold cache tier |
| PostgreSQL | 5432 | User config & API keys |
| Grafana | 3000 | Observability dashboard |

### Railway One-Click Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/infercache/infercache)

---

## API Usage

### Chat Completion

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'
```

### Health Check

```bash
curl http://localhost:8080/health
```

### Stats

```bash
curl http://localhost:8080/stats
```

Returns:
```json
{
  "hit_rate": 0.85,
  "memory_saved_mb": 124.5,
  "active_sessions": 42,
  "cost_savings_usd": 3.42
}
```

---

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Your App   │────▶│  InferCache      │────▶│  LiteLLM Proxy  │
│             │◀────│  Gateway (8080)  │◀────│  (4000)         │
└─────────────┘     └────────┬─────────┘     └────────┬────────┘
                             │                        │
                    ┌────────▼─────────┐     ┌────────▼────────┐
                    │  Redis (Hot)     │     │  OpenAI         │
                    │  TTL: 5 min      │     │  Anthropic      │
                    └────────┬─────────┘     │  Gemini         │
                             │               └─────────────────┘
                    ┌────────▼─────────┐
                    │  MinIO (Cold)    │
                    │  Long-term       │
                    └──────────────────┘
```

### Cache Flow

1. **Request arrives** at `/v1/chat/completions`
2. **Cache key** computed from model + messages hash
3. **Hot tier (Redis)** checked first — if hit, return immediately
4. **Cold tier (MinIO)** checked on miss — if found, promote to hot
5. **Upstream call** to LiteLLM on full miss
6. **Compress** response via OBCache and store in both tiers

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_PORT` | 8080 | Gateway port |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `MINIO_ENDPOINT` | localhost:9000 | MinIO endpoint |
| `MINIO_ACCESS_KEY` | minioadmin | MinIO access key |
| `MINIO_SECRET_KEY` | minioadmin | MinIO secret key |
| `MINIO_BUCKET` | infercache-cold | Cold cache bucket |
| `LITELLM_URL` | http://localhost:4000 | LiteLLM proxy URL |
| `CACHE_TTL_HOT` | 300 | Hot cache TTL (seconds) |
| `COMPRESSION_RATIO` | 10 | KV cache compression ratio |
| `DATABASE_URL` | postgresql://... | PostgreSQL connection |

---

## Testing

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# All tests
python -m pytest tests/ -v
```

---

## Grafana Dashboard

Access at `http://localhost:3000` (admin/admin).

Panels:
- **Cache Hit Rate** — percentage of requests served from cache
- **Memory Saved (MB)** — total KV cache memory saved via compression
- **Active Sessions** — currently active user sessions
- **Cost Savings (USD)** — estimated cost savings from cache hits
- **Hits vs Misses** — time-series of cache performance
- **Memory Over Time** — cumulative memory savings

---

## Compression

InferCache implements OBCache-style compression inspired by [NVIDIA KVPress](https://github.com/NVIDIA/KVPress):

1. **Chunkify** — split KV cache into fixed-size chunks
2. **Score** — compute saliency via byte-gram frequency (TF-IDF approximation)
3. **Select** — keep top-k chunks by score (k = total / ratio)
4. **Serialize** — compact binary blob with CRC-32 checksum

For a 100K-token context with ratio=10, this achieves **10x+ memory reduction** while preserving the most salient content.

---

## License

MIT
