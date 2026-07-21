# iframe 加载问题排障参考

当产品使用 iframe 嵌入外部服务（如 OpenMAIC），但 iframe 显示空白/错误/加载中时，
按以下步骤排查。

## 步骤一：确认后端服务是否正常运行

```
# 检查端口是否在监听
curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT/
```

如果返回非 200：
- 检查服务是否已启动（`ps aux | grep next|node`）
- 可能需要先安装依赖：`pnpm install`（node_modules 通常被 zip 排除）
- 如果本地缺 pnpm：`npm install -g pnpm`

## 步骤二：确认 iframe 的 data-src / 硬编码 URL

iframe 的目标 URL 可能来自：
- 硬编码：`http://localhost:3000`
- JS 函数：`OPENMAIC_URL` 返回动态 URL
- PHP 变量：`$openmaicUrl` 在 PHP 中设置
- data-src 属性：`data-src="http://localhost:PORT"` + JS 懒加载

查找方式：

```bash
grep -n "localhost:|AI_CLASS_IFRAME|OPENMAIC_URL|data-src" index.php | head -5
```

确保实际运行的 OpenMAIC/后端服务在同一个端口。

## 步骤三：检查 CSP（Content-Security-Policy）

这是 iframe 空白最常见的原因。

CSP 配置位置：`.env.local` 中的 `ALLOWED_FRAME_ANCESTORS`

致命错误：`http://localhost`（仅匹配 80 端口）
PHP 测试服务器运行在 localhost:161x 时，会被 CSP 拦截。

正确配置：`http://localhost:*`（通配符匹配所有端口）

验证方式：
```bash
# 查看 OpenMAIC 返回的 CSP 头
curl -sI http://localhost:PORT/ | grep -i frame-ancestors
```

三个模型的 CSP 配置差异（真实案例）：

| 模型 | ALLOWED_FRAME_ANCESTORS | iframe结果 | 根因 |
|------|------------------------|------------|------|
| jetty | http://localhost:* http://127.0.0.1:* | 正常加载 | 端口通配符 |
| orbit | http://localhost:* http://127.0.0.1:* | 空白页面 | JS渲染问题 |
| nimbus | http://localhost（仅80） | 错误图标 | CSP拦截 |

CSP 中的端口匹配规则：
- `http://localhost` = `http://localhost:80`（默认 HTTP 端口）
- `http://localhost:3000` = 仅匹配 3000 端口
- `http://localhost:*` = 匹配所有端口（推荐开发环境用这个）

## 步骤四：区分 CSP 拦截 vs JS 渲染失败

如果 CSP 正确（有 `:*`），但 iframe 仍然空白，很可能是 JS 渲染问题。

CSP 拦截的表现：
- 浏览器 DevTools Console 会报 `Refused to display ... in a frame because an ancestor violates CSP`
- iframe 显示错误图标（破损文件/小哭脸）

JS 渲染失败的表现：
- 没有 CSP 报错
- iframe 加载了文档但渲染空白
- 可能是 data-src 懒加载 + JS 执行时序问题

补充测试：
```bash
# 直接用 curl 访问 iframe URL 确认服务本身正常
curl -s http://localhost:PORT/ | grep -o '<title>[^<]*</title>'
```

## 步骤五：检查 PHP/HTML iframe 标签

对比不同模型的 iframe 标签写法：

```html
<!-- jetty 工作版本 -->
<iframe src="about:blank" allow="microphone;camera;clipboard-read;clipboard-write;autoplay" allowfullscreen></iframe>
<!-- JS 懒加载时设置为 OPENMAIC_URL -->

<!-- orbit 问题版本 -->
<iframe src="" data-src="http://localhost:3010" loading="lazy"></iframe>
<!-- JS 使用 data-src 设置 src；可能有执行时序问题 -->

<!-- nimbus CSP 问题版本 -->
<iframe id="aiIframe" src="" allow="microphone;camera;autoplay;fullscreen" style="display:none;"></iframe>
```

检查要点：
1. `src="about:blank"` vs `src=""` — 行为可能不同
2. `allow` 属性是否包含必要权限
3. `loading="lazy"` 是否影响加载
4. JS 中设置 `iframe.src` 的执行时机

## 真实案例：orbit iframe 空白（非 CSP 问题）

orbit 的 CSP 配置完全正确（`http://localhost:*`），且 OpenMAIC 服务也正常运行。
但 AI 课堂 iframe 仍显示空白页面。

根因分析：
问题出在 JS 懒加载方案上。orbit 使用 `data-src` + JS 设置 iframe src 的方式：

```html
<iframe id="aiClassroomIframe" src="" data-src="http://localhost:3010" loading="lazy"></iframe>
```

```javascript
if (aiIframe && !aiIframe.src && aiIframe.getAttribute('data-src')) {
    aiIframe.src = aiIframe.getAttribute('data-src');
}
```

可能的根因：
1. src 设置时序：`src=""`（空字符串）在有些浏览器中会被视为当前页面的 URL，
   触发一次导航。后续设置 data-src 可能被覆盖。
2. loading=lazy 延迟了 iframe 加载。
3. JS 事件绑定在 DOMContentLoaded 之前，导致 aiIframe 变量为 null。

对比 jetty 的工作方案：
```html
<iframe src="about:blank" ...></iframe>
```
```javascript
aiIframe.src = OPENMAIC_URL;
```
Jetty 使用 `about:blank` 作为初始 src（跨域安全），URL 直接赋值，
没有 data-src 中间步骤。

教训：
data-src 懒加载方案比直接 `src="about:blank"` + JS 设置 src 更容易出现
浏览器兼容性问题。评分时如果发现 iframe 空白：
1. 先检查 CSP（步骤三）
2. CSP 没问题则检查 iframe 标签写法
3. 记录为 JS 渲染问题而非 CSP 问题

## 快速排障模板

```bash
# 1. 确认后端服务
curl -sI http://localhost:PORT/ | head -5

# 2. 检查 CSP
curl -sI http://localhost:PORT/ | grep -i frame-ancestors

# 3. 确认 iframe URL
grep -n "localhost:|AI_CLASS_IFRAME|OPENMAIC_URL|data-src" index.php | head -5

# 4. 直接在新标签页打开 iframe URL 确认服务正常
# browser_navigate(url='http://localhost:PORT/')
```
