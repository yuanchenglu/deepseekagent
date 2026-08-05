// DeepAgent Worker — Landing page + R2 proxy + install.sh
// DEEPAGENT_RELEASES is a global R2 bucket binding

const CURRENT_VERSION = '0.9.0-alpha.1';

async function serveLandingPage() {
  const html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/><title>DeepAgent — 为 DeepSeek 定制的 AI Agent</title><meta name="description" content="为 DeepSeek 深度定制的 AI Agent"><style>*{margin:0;padding:0;box-sizing:border-box}body{background:#0A0E1A;color:#e0e0e0;font-family:system-ui,sans-serif;min-height:100vh;display:flex;justify-content:center;align-items:center}.c{text-align:center;padding:2rem;max-width:640px}h1{font-size:3rem;background:linear-gradient(135deg,#00D4FF,#FFBF00);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:.5rem}p{color:#888;margin-bottom:1rem}.code{background:#1a1f2e;padding:1rem;border-radius:8px;margin:1rem 0;color:#00D4FF;font-size:.9rem}a{display:inline-block;padding:.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:600;margin:.5rem}.p{background:#00D4FF;color:#0A0E1A}.s{border:1px solid #00D4FF;color:#00D4FF}.f{margin-top:2rem;color:#555;font-size:.85rem}</style></head><body><div class="c"><h1>DeepAgent</h1><p>为 DeepSeek 定制的 AI Agent — 一条命令安装，开箱即用</p><div class="code">curl -fsSL https://deepseekagent.starseas.org/install.sh | sh</div><a href="https://github.com/yuanchenglu/deepseekagent" class="p">GitHub</a><a href="/docs" class="s">文档</a><p class="f">© 2026 7ColorAI</p></div></body></html>`;
  return new Response(html, {
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=3600' }
  });
}

async function proxyFromR2(key) {
  // Rewrite only the CLI "latest" pointer (deepagent-latest.tar.gz), never
  // electron-updater's literal latest-mac.yml feed key.
  const resolvedKey = key.replace(/(?<=-)latest(?=\.)/, CURRENT_VERSION);
  const object = await DEEPAGENT_RELEASES.get(resolvedKey);
  if (object === null) {
    return new Response('Not Found: ' + resolvedKey, { status: 404 });
  }
  const headers = new Headers();
  object.writeHttpMetadata(headers);
  headers.set('Cache-Control', 'public, max-age=86400');
  headers.set('Access-Control-Allow-Origin', '*');
  return new Response(object.body, { headers, status: 200 });
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url);
  const path = url.pathname;

  if (path === '/install.sh') {
    return proxyFromR2('install-release.sh');
  }
  if (path.startsWith('/releases/')) {
    return proxyFromR2(path.replace('/releases/', ''));
  }
  return serveLandingPage();
}
