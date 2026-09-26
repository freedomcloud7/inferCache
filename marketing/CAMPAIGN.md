# InferCache Launch Campaign

## Positioning

**One-liner:** One API key. Every AI model. Flat $39/month.

**Angle:** OpenRouter charges per token. LiteLLM makes you self-host. InferCache is the drop-in OpenAI-compatible endpoint with a flat monthly price - predictable costs for people shipping AI products.

**Audience:** Indie hackers and devs building AI wrappers/agents who are tired of per-token billing surprises.

## Landing Page Copy

### Hero
> One key. Every model. $39/month.
>
> InferCache is an OpenAI-compatible LLM gateway. Point your existing code at our endpoint, swap one line, and get GPT-4o, Claude, Llama, DeepSeek and more - no per-token bills, no surprise invoices.

### Features
- Drop-in compatible - same /v1/chat/completions format as OpenAI. Your code works unchanged
- Every model - routed through OpenRouter full catalog
- Flat pricing - $39/month. That is the whole pricing page
- Your own key - unique, revocable API key per customer
- Always on - hosted on Railway with redundant replicas

### CTA
[Get your key - $39/mo](https://buy.stripe.com/bJe8wO0UP2UP1yz2EC9Ve01)

### FAQ
Cancel anytime - Keys delivered within minutes - Unlimited models, fair use

## Show HN Post

**Title:** Show HN: InferCache - OpenAI-compatible LLM gateway, flat $39/mo instead of per-token billing

I got tired of watching per-token costs creep up every month while building AI side projects. So I built a gateway: one endpoint, OpenAI-compatible API format, access to every model on OpenRouter, flat $39/month.

You get a personal API key, point your existing OpenAI client at our base URL, done. No SDK changes.

Tech: FastAPI on Railway, key-gated access, routes through OpenRouter catalog (GPT-4o, Claude, Llama, DeepSeek...).

Payment link is on the landing page. Happy to answer questions about the stack.

## Reddit - r/SideProject

**Title:** [Feedback wanted] I built a flat-rate LLM API gateway - $39/mo, every model, OpenAI-compatible

Per-token billing was killing my side projects economics. Built InferCache: swap your OpenAI base URL, use one key, call any model, pay one flat price.

Would love feedback on the landing page and whether flat-rate vs per-token matters to you.

## Reddit - r/LocalLLaMA

Flat-rate alternative to per-token API bills: I run an OpenAI-compatible gateway over OpenRouter catalog - $39/mo flat, one key, any model. Useful as a cloud fallback when your local rig cannot run the big stuff. AMA about the setup (FastAPI + Railway).

## X/Twitter Thread (build in public)

1. I got tired of per-token API bills eating my side projects alive. So I built my own LLM gateway. One key. Every model. $39/month flat.
2. It is OpenAI-compatible. Literally change your base URL and your existing code works. GPT-4o, Claude, Llama, DeepSeek - all through one endpoint.
3. No per-token anxiety. No surprise invoices. You pay $39, you get a key, you build. That is it.
4. Stack for the nerds: FastAPI on Railway, API-key gated, routes through @OpenRouter full catalog. 2 replicas, always on.
5. Just shipped v1.1.1 today: key auth, health checks, OpenRouter routing. Battle-tested with real completions before this tweet.
6. First 10 customers get founding-member pricing locked forever. Link in bio. Build something.

## Indie Hackers Post

**Title:** Milestone: Launched my LLM gateway - flat $39/mo vs per-token billing

Built it for myself first (my agents needed cheap, predictable model access). FastAPI + Railway + OpenRouter. Payment via Stripe Payment Links - zero billing code. Now opening to other builders. Roast my landing page.

## Product Hunt (Day 7)

- **Tagline:** One API key. Every AI model. Flat $39/month.
- **First comment:** Maker here - built this because per-token billing made side projects impossible to budget. AMA.

## 14-Day Calendar

| Day | Action |
|-----|--------|
| 1 | Landing page live + post X thread |
| 2 | Show HN (post Tue-Thu 9am ET for best odds) |
| 3 | r/SideProject post, reply to every comment |
| 4 | r/LocalLLaMA post |
| 5 | Indie Hackers milestone + 5 relevant Discord servers |
| 6 | Engage: answer 10 LLM-cost complaints on X with genuine help (no pitch) |
| 7 | Product Hunt launch |
| 8-14 | Follow-ups, customer onboarding, testimonial asks, repost wins |

## Metrics

- Stripe checkout completions (goal: 3 in week 1)
- Show HN upvotes/comments
- Landing page conversion (visits to checkout clicks)
- OpenRouter credit burn rate vs revenue

## Ops Note

Watch OpenRouter balance - flat-rate customers can burn credits fast. When the first Stripe payment lands, put ~$20 into OpenRouter credits. Later: add per-key usage caps to the gateway code.
