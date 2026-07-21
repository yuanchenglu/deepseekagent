---
name: cf-workers-ai-api-proxy-china
description: Deploy a free Cloudflare Workers proxy to access OpenAI, Claude, and other AI APIs from mainland China without VPN.
triggers:
  - "access openai api china without vpn"
  - "cloudflare workers ai api proxy"
  - "claude api china"
  - "openai api 国内访问"
  - "不翻墙使用openai api"
---

# Cloudflare Workers AI API Proxy for China Users

Use Cloudflare Workers to create a free, self-hosted proxy for accessing OpenAI, Claude, and other foreign AI APIs from mainland China without VPN.

## Problem

- OpenAI/Claude APIs are blocked or unreliable in China
- Third-party API relay services cost money and may be unreliable
- VPN is required to access API documentation and get API keys
- Need a solution that works without VPN for day-to-day API calls

## Solution: Cloudflare Workers Proxy

Deploy a simple proxy on Cloudflare Workers that forwards requests to OpenAI/Claude APIs. Workers uses Cloudflare's CDN which has nodes in China, making it accessible without VPN.

## Prerequisites

1. Cloudflare account (free)
2. OpenAI or Claude API key (obtained via VPN)
3. Basic understanding of JavaScript

## Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| Cloudflare Workers | **Free** | 100,000 requests/day free tier |
| Domain | **Free** | Uses xxx.workers.dev subdomain |
| API Usage | Variable | Pay OpenAI/Claude directly for token usage |

**Personal usage scenarios:**
- Light (100 calls/day): Free
- Medium (1,000 calls/day): Free
- Heavy (5,000 calls/day): Free
- Extreme (100,000 calls/day): $5/month paid plan

## Deployment Steps

### 1. Create Worker Script

In Cloudflare Dashboard:
1. Go to **Workers & Pages**
2. Click **Create Application**
3. Select **Create Worker**
4. Name your worker (e.g., `ai-api-proxy`)

### 2. Paste Proxy Code

Replace the default code with:

```javascript
// Cloudflare Workers AI API Proxy
// Supports: OpenAI, Anthropic Claude, Google Gemini

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    
    // Determine target API based on path prefix
    let targetBaseUrl;
    let apiKey;
    
    if (pathname.startsWith('/openai/')) {
      targetBaseUrl = 'https://api.openai.com';
      apiKey = env.OPENAI_API_KEY;
      // Remove the /openai prefix
      url.pathname = pathname.replace('/openai', '');
    } else if (pathname.startsWith('/anthropic/')) {
      targetBaseUrl = 'https://api.anthropic.com';
      apiKey = env.ANTHROPIC_API_KEY;
      url.pathname = pathname.replace('/anthropic', '');
    } else if (pathname.startsWith('/gemini/')) {
      targetBaseUrl = 'https://generativelanguage.googleapis.com';
      apiKey = env.GEMINI_API_KEY;
      url.pathname = pathname.replace('/gemini', '');
    } else {
      return new Response('Unknown API endpoint. Use /openai/, /anthropic/, or /gemini/', { status: 404 });
    }
    
    if (!apiKey) {
      return new Response(`API key not configured for this endpoint`, { status: 401 });
    }
    
    // Build target URL
    const targetUrl = targetBaseUrl + url.pathname + url.search;
    
    // Clone and modify request headers
    const headers = new Headers(request.headers);
    headers.set('Authorization', `Bearer ${apiKey}`);
    headers.set('Host', new URL(targetBaseUrl).host);
    
    // Remove CF-specific headers that might cause issues
    headers.delete('cf-ray');
    headers.delete('cf-visitor');
    headers.delete('cf-connecting-ip');
    
    // Forward the request
    const modifiedRequest = new Request(targetUrl, {
      method: request.method,
      headers: headers,
      body: request.body,
    });
    
    try {
      const response = await fetch(modifiedRequest);
      
      // Create new response with CORS headers
      const newHeaders = new Headers(response.headers);
      newHeaders.set('Access-Control-Allow-Origin', '*');
      newHeaders.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      newHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    } catch (error) {
      return new Response(`Proxy error: ${error.message}`, { status: 502 });
    }
  },
};
```

### 3. Configure Environment Variables

1. Go to your Worker's **Settings** tab
2. Click **Variables**
3. Add your API keys:
   - `OPENAI_API_KEY` = your OpenAI API key
   - `ANTHROPIC_API_KEY` = your Claude API key
   - `GEMINI_API_KEY` = your Gemini API key (optional)

### 4. Deploy

Click **Save and Deploy**. Your proxy is now live at:
`https://your-worker-name.your-subdomain.workers.dev`

## Usage

### OpenAI API

Replace in your code:
```python
# Before (requires VPN)
base_url = "https://api.openai.com/v1"

# After (works in China)
base_url = "https://your-worker.workers.dev/openai/v1"
```

Example with OpenAI Python SDK:
```python
from openai import OpenAI

client = OpenAI(
    api_key="your-openai-key",
    base_url="https://your-worker.workers.dev/openai/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Claude API

```python
# Before
base_url = "https://api.anthropic.com/v1"

# After
base_url = "https://your-worker.workers.dev/anthropic/v1"
```

## Security Considerations

1. **Keep API keys secret** - Store in Workers environment variables, never in code
2. **Rate limiting** - Consider adding rate limiting to prevent abuse
3. **Authentication** - For production, add your own auth layer
4. **CORS** - Script includes basic CORS headers for browser access

## Troubleshooting

### Worker returns 401
- Check that API key is correctly set in environment variables
- Verify key has not expired

### Worker returns 502
- Target API may be temporarily down
- Check Cloudflare status page

### Slow response times
- Workers free tier has CPU time limits
- For production use, consider Workers Paid plan ($5/month)

### CORS errors in browser
- Script includes CORS headers, but some APIs may require additional handling
- Check browser console for specific errors

## Alternative: Using Wrangler CLI

For advanced users, deploy via CLI:

```bash
# Install Wrangler
npm install -g wrangler

# Login
wrangler login

# Create project
wrangler init ai-proxy

# Deploy
wrangler deploy
```

## Comparison with Other Solutions

| Solution | Cost | Setup Complexity | Reliability |
|----------|------|------------------|-------------|
| CF Workers Proxy | Free | Medium | High |
| OpenRouter | Free | Low | Medium |
| Third-party relay | ¥10-100+/month | Low | Variable |
| Self-hosted VPS | $5-10/month | High | High |
| VPN | $3-10/month | Low | Variable |

## Pitfalls

1. **Free tier limits** - 100k requests/day; monitor usage in CF dashboard
2. **CPU time** - 10ms per request on free tier; streaming responses may hit limits
3. **Cold starts** - First request after idle may be slower
4. **API key exposure** - Never commit keys to git; always use environment variables

## References

- Cloudflare Workers Docs: https://developers.cloudflare.com/workers/
- OpenAI API Docs: https://platform.openai.com/docs
- Anthropic API Docs: https://docs.anthropic.com/
