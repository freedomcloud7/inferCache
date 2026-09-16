# Railway Template Publishing Guide

## Navigate to Template Composer

1. Go to: https://railway.com/workspace/templates/5ea439bc-5fce-4517-a2c3-9ef8dcba48e3/marketplace

   If that link fails:
   - Go to https://railway.app/project/authentic-courage/settings
   - Scroll to bottom → click "Generate Template from Project"
   - Click "Create Template"

---

## Step 1: Short Description

Set the Short Description field to:

```
KV-cache-optimized LLM gateway. 10x compression, Redis caching, and multi-provider routing.
```

---

## Step 2: Overview (Write tab)

Paste this into the Overview field:

```markdown
# Deploy and Host InferCache on Railway

InferCache is a transparent proxy that compresses LLM KV cache to reduce memory usage by up to 10x. It allows you to serve more concurrent sessions on the same hardware and cuts inference costs.

# About Hosting InferCache

Deploy this template to instantly spin up a FastAPI gateway with Redis hot caching and an Ollama backend for free local LLM inference. The gateway intercepts requests, compresses the KV cache, and stores it in Redis.

# Why Deploy InferCache

Reduce LLM API costs and serve more concurrent users without adding hardware.

# Common Use Cases

- Running long-context AI agents without running out of memory
- Serving multiple concurrent users on a single GPU or CPU
- Reducing LLM API costs by caching repeated prompts

# Dependencies for InferCache Hosting

- Redis (included in this template)
- Ollama (included in this template)
- Optional: Anthropic or OpenRouter API keys for cloud models
```

---

## Step 3: Variable Descriptions

Click each variable on the left and paste the corresponding description:

| Variable | Description |
|----------|-------------|
| `ollama.OLLAMA_HOST` | The host address for the Ollama API service. |
| `Redis.REDISHOST` | The internal hostname for the Redis service. |
| `Redis.REDISPORT` | The port for Redis (default: 6379). |
| `Redis.REDISUSER` | The username for Redis (default: default). |
| `Redis.REDIS_URL` | The internal connection URL for Redis. |
| `Redis.REDISPASSWORD` | The password for the Redis service. |
| `authentic-courage.REDIS_URL` | The internal connection URL for Redis. |
| `authentic-courage.LITELLM_URL` | The base URL for the LLM provider (Ollama). |
| `authentic-courage.MINIO_ENDPOINT` | Endpoint for MinIO cold storage (optional). |
| `authentic-courage.MINIO_ACCESS_KEY` | MinIO access key (optional). |
| `authentic-courage.MINIO_SECRET_KEY` | MinIO secret key (optional). |

---

## Step 4: Icons

1. Click on the **authentic-courage** service box (middle of canvas)
2. In settings panel on right → find **Icon** setting → choose 🧠

3. Click on the **Redis** service box
4. In settings panel → find **Icon** setting → choose 🗄️

---

## Step 5: Publish

1. Click the purple **"Apply"** button (top right corner)
2. Wait for red X's on left to turn into green checkmarks
3. Click the purple **"Publish to Marketplace"** button (bottom left corner)

---

## Done!

You should see a success message confirming the template was published.
