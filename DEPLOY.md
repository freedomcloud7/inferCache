# Deploying InferCache to Railway

## 🚀 EASIEST: Single API Key via OpenRouter

**Just ONE environment variable** and you're ready:

```bash
# Link to project
railway link --project authentic-courage

# Set ONE key (covers ALL models: GPT, Claude, Gemini, etc.)
railway variables set OPENROUTER_API_KEY=your-openrouter-key

# Deploy
railway up -d
```

---

## 📋 Get OpenRouter API Key (Free & Paid Tiers Available)

1. Go to: https://openrouter.ai/api-keys
2. Click "Get API Key"
3. Copy the key (starts with `sk-or-v1-...`)
4. Use in Railway as shown above

### Why OpenRouter?
- ✅ Single API key for ALL models
- ✅ Free tier available (200K tokens/month)
- ✅ Pay-as-you-go on overage
- ✅ No need for separate OpenAI/Anthropic/Gemini keys

---

## 🔧 Alternative: Direct Provider Keys

If you prefer direct keys:

```bash
# Link to project
railway link --project authentic-courage

# Set keys (pick what you have)
railway variables set OPENAI_API_KEY=sk-your-openai-key
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key
railway variables set GEMINI_API_KEY=your-gemini-key

# Deploy
railway up -d
```

---

## ⚡ Local Ollama (Optional)

If you have Ollama running locally:

```bash
railway variables set OLLAMA_URL=http://localhost:11434
```

---

## 📊 After Deployment

**Health Check:**
```bash
curl https://your-app.up.railway.app/health
```

**Test with popular models:**
```bash
# Using OpenRouter (free models)
curl -X POST https://your-app.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"meta-llama/llama-3.1-8b-instant","messages":[{"role":"user","content":"Hello"}]}'
```

---

## 📦 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OR API key (supports all models) | ✅ Preferred |
| `OPENAI_API_KEY` | OpenAI API key | Alternative |
| `ANTHROPIC_API_KEY` | Anthropic API key | Alternative |
| `GEMINI_API_KEY` | Google Gemini API key | Alternative |
| `OLLAMA_URL` | Local Ollama endpoint | Optional |

---

## 🔗 Model References

**OpenRouter models (free tier):**
- `meta-llama/llama-3.1-8b-instant` - Llama 3.1 8B
- `meta-llama/llama-3.1-70b-instant` - Llama 3.1 70B  
- `google/gemini-2.0-flash` - Gemini 2.0
- `anthropic/claude-sonnet-4-20250929` - Claude Sonnet 4

**Direct keys (usage-based):**
- `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku`
- `gemini-pro`, `gemini-1.5-pro`

---

## ✅ Current Status

- Code committed and pushed to GitHub
- Dependencies simplified
- Dockerfile updated  
- Application working locally
- **Ready for OpenRouter deployment** (single key!)