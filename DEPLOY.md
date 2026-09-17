# Deploying InferCache to Railway

## Quick Start

1. **Login to Railway CLI**:
   ```bash
   npx @railway/cli login
   ```

2. **Link to existing project** (if exists) or create new:
   ```bash
   # Link to existing authentic-courage project
   railway link --project authentic-courage
   
   # Or create new project
   railway init
   ```

3. **Set environment variables**:
   ```bash
   railway variables set OPENAI_API_KEY=sk-your-key
   railway variables set ANTHROPIC_API_KEY=sk-ant-your-key
   railway variables set GEMINI_API_KEY=your-gemini-key
   ```

4. **Deploy**:
   ```bash
   railway up -d
   ```

## Environment Variables Required

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | ✅ |
| `ANTHROPIC_API_KEY` | Anthropic API key | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key | ✅ |

## Health Check

After deployment, check the health endpoint:
```bash
curl https://your-app.up.railway.app/health
```

Expected response:
```json
{"status":"ok","service":"infercache-gateway"}
```

## Testing the API

```bash
curl -X POST https://your-app.up.railway.app/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}'
```

## Rollback

If something goes wrong:
```bash
railway down
```

## Current Status

✅ Code is committed and pushed to GitHub
✅ Dependencies simplified
✅ Dockerfile updated
✅ Application working locally on port 8000