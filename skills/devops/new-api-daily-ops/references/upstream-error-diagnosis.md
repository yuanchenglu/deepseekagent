# NewAPI 上游错误诊断：OpenClash / Fake-IP 干扰

## 问题特征

NewAPI 健康监测或客户反馈报：

```
upstream error: do request failed (request id: ...)
```

底层错误为：
- `connection reset by peer` — TCP 连接被代理服务器重置
- `EOF` — 代理服务器无响应
- `read: connection reset by peer`

**原因：** OpenClash 将 AI API 域名通过 Fake-IP 劫持后路由到代理服务器，代理不稳定时导致连接中断。

## 快速诊断三步

### 1. 检查 DNS 是否被 Fake-IP 劫持

```bash
dig +short opencode.ai
# 如果返回 198.18.x.x → 被 Clash Fake-IP 劫持
# 如果返回正常公网 IP → DNS 正常
```

### 2. 获取真实 IP 对比

```bash
# 通过 DoH（DNS over HTTPS）绕过 OpenClash 劫持
curl -s "https://dns.google/resolve?name=opencode.ai&type=A" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print('真实IP:', d.get('Answer',[{}])[0].get('data','?'))"
```

### 3. 确认是否走代理

```bash
# 看出口 IP（不是你家宽 IP 就说明走代理了）
curl -s https://api.ipify.org

# 看容器日志确认哪个 channel 报错
sudo docker logs new-api 2>&1 | grep "upstream error" | tail -10
# 输出示例: "channel error (channel #3, status code: 500): upstream error: do request failed"
# 找到对应的 channel_id 后查渠道：
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, base_url FROM channels WHERE id = 3;"
```

## 受影响域名清单

以下 AI API 域名可能被 OpenClash 劫持，应加入 Fake-IP 白名单：

| 域名 | 用途 |
|------|------|
| `opencode.ai` | NewAPI 上游（OpenCode Go） |
| `token.clawadmin.org` | NewAPI 自身域名 |
| `api.anthropic.com` | Anthropic API（代理中继场景） |
| `api.openai.com` | OpenAI API（代理中继场景） |
| `api.deepseek.com` | DeepSeek API（代理中继场景） |

## 修复

详见 `openclash-whitelist-manager` skill：
- 将域名加入 OpenClash 的 `openclash_custom_fake_filter.list`
- 或设置 OpenClash 为 「GFW 白名单模式」（只有 GFW 清单域名走代理）

---

## 另一个常见错误：DeepSeek — "Empty input messages"

### 问题特征

NewAPI 健康监测或 API 调用报：

```
Error from provider (DeepSeek): Empty input messages
```

日志中 channel 为 **Anthropic 类型（type=14）** 的渠道。

### 根因

**DeepSeek 模型被路由到了 Anthropic 格式渠道。** NewAPI 的渠道类型（type）决定请求的序列化格式：

| 渠道类型 | 序列化格式 | 适用模型 |
|---------|-----------|---------|
| type=1 (OpenAI) | `POST /v1/chat/completions`, Authorization header | OpenAI、DeepSeek、通义千问 等 |
| type=14 (Anthropic) | `POST /v1/messages`, x-api-key header | Claude、兼容 Anthropic 格式的模型 |

当 `deepseek-v4-flash` / `deepseek-v4-pro` 只配在 type=14 的 Anthropic 渠道上时，NewAPI 会将 OpenAI 格式请求转换为 Anthropic 格式再发出。DeepSeek 的 API 无法解析转换后的 Anthropic 格式 payload，返回 `Empty input messages`。

### 快速诊断

```bash
# 1. 查 deepseek 模型在哪个渠道上
sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT channel_id, model, enabled FROM abilities WHERE model LIKE '%deepseek%';"

# 2. 确认渠道类型
sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, type, models FROM channels WHERE id = <channel_id>;"

# 3. 直接验证：通过 OpenAI 格式调 deepseek（应成功）
curl -s --max-time 20 -X POST https://opencode.ai/zen/go/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-xxxx' \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}]}'
# ✅ 成功 → 说明 DeepSeek 本身正常，是 NewAPI 渠道类型不对
```

### 修复

```bash
# 从 Anthropic 渠道移除 deepseek，添加到 OpenAI 渠道

# 1. 先查当前模型列表
sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, type, models FROM channels WHERE id=3 OR id=4;"

# 2. 更新渠道模型列表
sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET models = 'deepseek-v4-flash,deepseek-v4-pro,其他已有模型...' WHERE id = <OpenAI渠道ID>;"

sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET models = '去掉deepseek后的模型列表' WHERE id = <Anthropic渠道ID>;"

# 3. ⚠️ 关键：禁用 Anthropic 渠道的上游自动同步
#    否则重启后 NewAPI 会从 OpenCode Go 重新拉模型列表，又把 deepseek 加回去
sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET settings = '{\"upstream_model_update_auto_sync_enabled\":false}' WHERE id = <Anthropic渠道ID>;"

# 4. 重启 NewAPI
sudo kill $(pgrep -x new-api | tail -1); sleep 2; /new-api &

# 5. 验证 abilities 表
sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT channel_id, model FROM abilities WHERE model LIKE '%deepseek%';"
# 预期输出：只在 OpenAI 渠道（type=1），不能在 Anthropic 渠道（type=14）

# 6. 如果 abilities 为空（auto-sync 关闭后重启可能不重建），手动插入：
#    INSERT INTO abilities ("group", model, channel_id, enabled, priority, weight)
#    VALUES ('default', 'deepseek-v4-flash', 3, 1, 0, 1);
#    完整模型列表见 SKILL.md 操作十二
```

### 注意（陷阱）

#### ⚠️ 陷阱一：上游自动同步（auto-sync）— 根源级风险

NewAPI v1.0.0-rc.14 **默认对每个渠道启用** `upstream_model_update_auto_sync_enabled`。启动时会查询上游的 `/v1/models` 端点，把上游返回的**所有模型**自动匹配到每个渠道的 abilities 表中。这个行为是绕开 `channels.models` 字段的。

这意味着一个严重的回归链路：

```
改了 channels.models（移除 DeepSeek）
  → 重启 NewAPI
    → auto-sync 发现上游有 deepseek-v4-flash
      → 自动 INSERT 进 abilities，channel_id=Anthropic渠道
        → DeepSeek 又走错渠道了
          → 又报 "Empty input messages"
```

**结论：Anthropic 渠道（type=14）必须永远关掉 auto-sync：**
```sql
UPDATE channels SET settings = '{"upstream_model_update_auto_sync_enabled":false}' WHERE id = <Anthropic渠道ID>;
```

#### 陷阱二：abilities 表需手动重建

当 auto-sync 关闭后，启动时 abilities 表可能为空：
```bash
# 如果返回 0，需要手动 INSERT
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT COUNT(*) FROM abilities WHERE channel_id IN (3,4);"
```

手动重建见下表。

#### 陷阱三：同一个 OpenCode Go key 可以用在两个渠道

同一个 key 同时用于 OpenAI 和 Anthropic 渠道没问题——OpenCode Go 根据请求路径区分格式：
- `/v1/chat/completions` → OpenAI 格式
- `/v1/messages` → Anthropic 格式

key 本身是一样的。

#### 陷阱四：重启命令因部署方式而异

| 部署方式 | 重启命令 |
|---------|---------|
| 本机二进制 | `sudo kill $(pgrep -x new-api | tail -1); sleep 2; /new-api &` |
| Docker | `sudo docker restart new-api` |

---

### 完整模型分配表（OpenCode Go，2026-06-25）

| 渠道 | 格式 | 模型 |
|------|------|------|
| **Ch3 - OpenAI** (type=1) | OpenAI `/v1/chat/completions` | `deepseek-v4-flash,deepseek-v4-pro,glm-5.2,glm-5.1,glm-5,kimi-k2.7,kimi-k2.6,kimi-k2.5,mimo-v2.5,mimo-v2.5-pro,mimo-v2-pro,mimo-v2-omni,qwen3.5-plus,hy3-preview` |
| **Ch4 - Anthropic** (type=14) | Anthropic `/v1/messages` | `minimax-m3,minimax-m2.7,minimax-m2.5,qwen3.7-max,qwen3.7-plus,qwen3.6-plus` |

abilities 重建 SQL：
```bash
# Ch3 (OpenAI 格式)
for m in deepseek-v4-flash deepseek-v4-pro glm-5.2 glm-5.1 glm-5 kimi-k2.7 kimi-k2.6 kimi-k2.5 mimo-v2.5 mimo-v2.5-pro mimo-v2-pro mimo-v2-omni qwen3.5-plus hy3-preview; do
  sudo sqlite3 /home/bluth/new-api/data/one-api.db \
    "INSERT OR IGNORE INTO abilities (\"group\", model, channel_id, enabled, priority, weight) VALUES ('default', '$m', 3, 1, 0, 1);"
done

# Ch4 (Anthropic 格式)
for m in minimax-m3 minimax-m2.7 minimax-m2.5 qwen3.7-max qwen3.7-plus qwen3.6-plus; do
  sudo sqlite3 /home/bluth/new-api/data/one-api.db \
    "INSERT OR IGNORE INTO abilities (\"group\", model, channel_id, enabled, priority, weight) VALUES ('default', '$m', 4, 1, 0, 1);"
done
```

### 上游模型列表变更处理流程

当 OpenCode Go 更新了模型列表（新增/下架），**用户通知我，我来手动处理：**

1. 去 OpenCode Go 文档（https://opencode.ai/docs/zh-cn/go/）看更新后的模型列表
2. 按格式分组：OpenAI 格式（`/v1/chat/completions`）vs Anthropic 格式（`/v1/messages`）
3. 更新两个渠道的 `channels.models` 字段
4. 同步更新 `abilities` 表（INSERT OR IGNORE 新增模型）
5. 重启验证

**绝不打开 Anthropic 渠道的 auto-sync。**

---

## 注意

- 即使问题「过一会儿自己好了」，根因仍然存在（代理下次抽风还会出问题）
- 不是每次都会触发——只有代理服务器不稳定时才会
- 直连真实 IP 始终正常工作
