---
name: new-api-daily-ops
description: NewAPI 日常运维终端操作手册——改余额、查Token、重置密码等Web UI做不了的事。本机SQLite直接操作，命令即用即走。
version: 1.2.0
triggers:
  - "改余额"
  - "改token余额"
  - "查token"
  - "重置密码"
  - "newapi操作"
  - "NewAPI怎么操作"
  - "怎么看token"
  - "怎么改额度"
  - "创建渠道"
  - "添加渠道"
  - "创建用户"
  - "创建套餐"
  - "创建订阅计划"
  - "推理强度"
  - "reasoning"
  - "强化推理"
  - "健康监测"
  - "健康检查"
  - "监控"
  - "Empty input messages"
  - "渠道类型不匹配"
  - "模型走错渠道"
  - "自动同步"
  - "auto-sync"
  - "upstream model sync"
  - "上游更新模型"
  - "模型列表变了"
  - "token失效"
  - "token状态"
  - "Invalid token"
  - "token额度"
  - "token还有多少"
  - "token用完了"
---

# NewAPI 日常运维操作手册

**核心认知：NewAPI Web UI 能做什么、不能做什么**

| 操作 | Web UI | 终端（本Skill） | 说明 |
|------|--------|----------------|------|
| 创建渠道 | ✅ 能 | ✅ 操作六 | UI 更方便；终端备用 |
| 创建用户 | ✅ 能 | ✅ 操作七 | UI 更方便；终端备用 |
| 创建套餐 | ❌ v1.0.0-rc.10 未暴露 | ✅ 操作八 | 只能终端 |
| 给自己创建 Token | ✅ 能 | - | 登录后自己创建 |
| **给别人创建 Token** | ❌ 不能 | ✅ 操作三 | API 限制，只能终端 |
| **改别人的 Token 余额** | ❌ 不能 | ✅ 操作一 | 改 remain_quota 字段 |
| **查看完整 Key** | ❌ 掩码 | ✅ 操作二 | UI 只显示 sk-xxx...xxx |
| **重置密码** | ❌ 不能 | ✅ 操作五 | bcrypt 哈希坏了只能终端 |
| 禁用/启用 Token | ❌ 不能 | ✅ 操作四 | status=1/2 |
| 查所有渠道 | ✅ 能 | ✅ 操作九 | 终端更直观 |
| 查所有用户 | ✅ 能 | ✅ 操作十 | 终端更直观 |

**本机环境：**
- 数据库：`/home/bluth/new-api/data/one-api.db`（SQLite3）
- 部署方式：**本机二进制**（`/new-api`，非 Docker）或 **Docker 容器**（`new-api`）
- 所有 SQLite 操作需要 `sudo`
- 重启命令：
  - 本机二进制：`sudo kill $(pgrep -x new-api | tail -1); sleep 2; /new-api &`
  - Docker：`sudo docker restart new-api`

---

## 操作一：改 Token 余额（不改 Key）

**场景：** 客户 key 已分发，只想改余额，不换 key。

```bash
# 1. 先查当前余额
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, key, remain_quota, unlimited_quota FROM tokens WHERE name='customer01';"

# 2. 改余额（这里改成 2 亿 = 200000000）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE tokens SET remain_quota = 200000000 WHERE name='customer01';"

# 3. 确认改成功
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, remain_quota FROM tokens WHERE name='customer01';"

# 4. 重启容器让缓存生效（必须！）
sudo docker restart new-api
```

**余额单位：** tokens（1 亿 = 100000000，10 亿 = 1000000000）

---

## 操作二：查看所有 Token（完整 Key + 余额）

```bash
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, key, remain_quota, unlimited_quota, status FROM tokens;"
```

**输出解读：**
- `key`：完整 48 位字符，给客户时加 `sk-` 前缀
- `remain_quota`：剩余 tokens，负数 = 已超用
- `unlimited_quota`：1 = 无限额度，0 = 有限
- `status`：1 = 启用，2 = 禁用

---

## 操作三：为其他用户创建 Token

**场景：** 创建了用户 `customer01`，但没法在 Web UI 给他创建 key。

```bash
# 1. 先查用户的 ID
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, username, group_q FROM users WHERE username='customer01';"

# 2. 生成 48 位随机 key（用 Python）
python3 -c "
import random
chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
key = ''.join(random.choices(chars, k=48))
print(key)
"

# 3. 插入数据库（把 <user_id>、<生成的key>、<token名称> 替换）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO tokens (user_id, name, key, status, created_time, accessed_time,
   expired_time, remain_quota, unlimited_quota, \"group\")
   VALUES (<user_id>, '<token名称>', '<生成的48位key>', 1,
   strftime('%s','now'), strftime('%s','now'), -1, 1000000000, 0, 'default');"

# 4. 重启
sudo docker restart new-api
```

**给客户显示的 Key：** 把 48 位字符前面加 `sk-`（如 `sk-MuHY7SKJuAsiMrAAxc2e8mW3hq9Uo7eIGUiSQIFNjGYcxOrM`）

---

## 操作四：禁用/启用 Token

```bash
# 禁用（status=2）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE tokens SET status = 2 WHERE name='customer01';"

# 启用（status=1）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE tokens SET status = 1 WHERE name='customer01';"

# 必须重启
sudo docker restart new-api
```

---

## 操作五：重置管理员密码

**场景：** 登录提示"用户名或密码错误"，但密码没改过——bcrypt 哈希损坏。

```bash
# 1. 生成新 bcrypt 哈希
python3 -c "
import bcrypt
password = b'Lu653426595.'
salt = bcrypt.gensalt(rounds=10)
new_hash = bcrypt.hashpw(password, salt)
print(new_hash.decode())
"

# 2. 更新数据库（把 <新哈希> 替换为上一步输出）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE users SET password='<新哈希>' WHERE username='bluth';"

# 3. 重启
sudo docker restart new-api && sleep 2

# 4. 验证
curl -s -X POST http://localhost:3000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"bluth","password":"Lu653426595."}'
# 预期返回："success":true
```

---

## 操作六：创建渠道

**两种方式：**

### 方式 A：Web UI（推荐）
1. 登录 `https://token.clawadmin.org` → 渠道 → 添加渠道
2. 填好名称、类型、Key、Base URL、模型列表 → 提交

### 方式 B：终端直接插入（Web UI 抽风时备用）

```bash
# 创建 OpenAI 格式渠道（type=1）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO channels (type, key, status, name, weight, created_time,
   base_url, models, \"group\", priority, auto_ban)
   VALUES (1, 'sk-rDf1tdVPedjoNsNTeiZEBnilWXoMJJE5DpxmvNlgo6e3weAXKiPSweMJ1grWY6ht',
   1, 'OpenCode Go - OpenAI', 1, strftime('%s','now'),
   'https://opencode.ai/zen/go',
   'deepseek-v4-flash,deepseek-v4-pro,glm-5.1,glm-5,kimi-k2.6,kimi-k2.5',
   'default', 0, 0);"

# 创建 Anthropic 格式渠道（type=14）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO channels (type, key, status, name, weight, created_time,
   base_url, models, \"group\", priority, auto_ban)
   VALUES (14, 'sk-rDf1tdVPedjoNsNTeiZEBnilWXoMJJE5DpxmvNlgo6e3weAXKiPSweMJ1grWY6ht',
   1, 'OpenCode Go - Anthropic', 1, strftime('%s','now'),
   'https://opencode.ai/zen/go',
   'qwen3.7-max,qwen3.7-plus,qwen3.6-plus,minimax-m3,minimax-m2.7,minimax-m2.5',
   'default', 0, 0);"

# 必须重启
sudo docker restart new-api
```

**渠道类型对照：**
- `1` = OpenAI（自动追加 `/v1/chat/completions`）
- `14` = Anthropic（自动发 `x-api-key` + `anthropic-version` 头）
- `37` = 阿里通义

**注意：** Type=1 的 base_url 不要以 `/v1` 结尾，NewAPI 会自动追加。

---

## 操作七：创建用户

```bash
# 先安装 bcrypt（如果没有）
pip3 install bcrypt -q

# 生成密码哈希
python3 -c "
import bcrypt
password = b'用户密码'
salt = bcrypt.gensalt(rounds=10)
new_hash = bcrypt.hashpw(password, salt)
print(new_hash.decode())
"

# 插入用户（把 <哈希值> 替换为上一步输出）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO users (username, password, display_name, role, status, \"group\", quota)
   VALUES ('customer02', '<哈希值>', 'Customer 02', 1, 1, 'default', 0);"

# 必须重启
sudo docker restart new-api
```

**角色对照：**
- `100` = root 管理员
- `10` = 普通管理员
- `1` = 普通用户

---

## 操作八：创建套餐（订阅计划）

```bash
# 99元套餐：1 亿 tokens/月
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO subscription_plans (title, subtitle, price_amount, currency,
   duration_unit, duration_value, enabled, upgrade_group, total_amount, quota_reset_period)
   VALUES ('99元月卡', '1亿tokens/月', 99, 'CNY',
   'month', 1, 1, 'default', 100000000, 'month');"

# 199元套餐：3 亿 tokens/月
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO subscription_plans (title, subtitle, price_amount, currency,
   duration_unit, duration_value, enabled, upgrade_group, total_amount, quota_reset_period)
   VALUES ('199元月卡', '3亿tokens/月', 199, 'CNY',
   'month', 1, 1, 'default', 300000000, 'month');"

# 499元套餐：8 亿 tokens/月
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO subscription_plans (title, subtitle, price_amount, currency,
   duration_unit, duration_value, enabled, upgrade_group, total_amount, quota_reset_period)
   VALUES ('499元月卡', '8亿tokens/月', 499, 'CNY',
   'month', 1, 1, 'default', 800000000, 'month');"

# 999元套餐：20 亿 tokens/月
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "INSERT INTO subscription_plans (title, subtitle, price_amount, currency,
   duration_unit, duration_value, enabled, upgrade_group, total_amount, quota_reset_period)
   VALUES ('999元月卡', '20亿tokens/月', 999, 'CNY',
   'month', 1, 1, 'default', 2000000000, 'month');"

# 查看已创建的套餐
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, title, price_amount, total_amount FROM subscription_plans;"

# 必须重启
sudo docker restart new-api
```

**字段说明：**
- `title`：套餐名称（显示给用户）
- `price_amount`：价格（配合 currency 使用）
- `total_amount`：包含的 tokens 总量
- `quota_reset_period`：额度重置周期（`month`/`never`）
- `upgrade_group`：订阅后用户 token 自动切换到的 group（一般用 `default`）

---

## 操作九：查看所有渠道

```bash
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, name, type, base_url, models, status FROM channels;"
```

**渠道类型对照：**
- 1 = OpenAI（自动追加 `/v1/chat/completions`）
- 14 = Anthropic（自动发 `x-api-key` + `anthropic-version` 头）
- 37 = 阿里通义

---

## 操作十：查看所有用户

```bash
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT id, username, role, status, \"group\" FROM users;"
```

---

## 操作十一：强制开启 DeepSeek 最高推理

**场景：** 不管客户端传不传 `reasoning_effort`，渠道侧强制注入最高推理档。

```bash
# 对渠道 ID=3 设置 param_override = max（DeepSeek V4 最高推理档）
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET param_override = '{\"reasoning_effort\":\"max\"}' WHERE id = 3;
   SELECT id, name, param_override FROM channels WHERE id = 3;"

# 必须重启
sudo docker restart new-api
```

**验证（客户端不传 reasoning_effort，看是否自动生效）：**
```bash
curl -s -X POST http://localhost:3000/v1/chat/completions \
  -H "Authorization: Bearer sk-SzgIhKM0KS2e1UH6iwBrrR8jfXKEHqukeIBwsCFsu3eP0z8a" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"1+1=?"}],"max_tokens":60}'
```
响应中 `completion_tokens_details.reasoning_tokens` 数值显著高于默认即可确认生效。

**已知影响：** `max` 比 `high` 多消耗 ~60% 推理 tokens，但任务完成质量更高。对非 DeepSeek 模型（GLM、Kimi）安全——它们会忽略不认识参数。

**原理：** NewAPI 的 `param_override` 字段（JSON）中的键值对会在转发请求时强制合并进 body。客户端传了会被覆盖，没传会被注入。注意：OpenCode Go 直接接受 `max`，不需要像 Hermes 那样用 `xhigh` 做中间映射。

---

---

## 核心教训：上游自动同步陷阱 ⚠️（2026-06-25 实战）

**NewAPI 的 `upstream_model_update_auto_sync_enabled` 默认开启。** 对 Anthropic 格式渠道（type=14）来说，**这个开关必须关掉**。

### 为什么

NewAPI 启动时会查询上游（OpenCode Go）的 `/v1/models` 端点，把上游返回的所有模型加到每个渠道的 abilities 表中——**无视你手动设的 models 字段**。

这意味着：
1. 你把 DeepSeek 从 Anthropic 渠道的 models 字段删了
2. 重启 NewAPI
3. auto-sync 发现上游有 deepseek-v4-flash → **自动加回 Anthropic 渠道**
4. DeepSeek 再次走错渠道 → 又报 "Empty input messages"

### 必须做的事

```
Anthropic 渠道（type=14）→ upstream_model_update_auto_sync_enabled = false
OpenAI 渠道（type=1）    → 可以保持 true（OpenAI 格式不会格式转换问题）
```

### 如果上游模型列表变了怎么办

你说过的：**你通知我，我来手动处理。** 流程：

1. 你告诉我"OpenCode Go 更新了模型列表"
2. 我去看看新增/删除了哪些模型
3. 按格式（OpenAI / Anthropic）分配到对应渠道
4. 更新 channels.models + abilities
5. 重启验证

**绝不打开 Anthropic 渠道的 auto-sync。**

---

**场景：** NewAPI 代理 OpenCode Go 时，模型走错渠道导致 "Empty input messages"。

### 核心原则

OpenCode Go 的模型使用两种不同的 API 格式，NewAPI 渠道的 type 必须匹配：

| 模型 | 模型 ID | 请求格式 | NewAPI channel type |
|------|---------|---------|-------------------|
| DeepSeek V4 Pro | `deepseek-v4-pro` | OpenAI（`/v1/chat/completions`） | type=1 |
| DeepSeek V4 Flash | `deepseek-v4-flash` | OpenAI | type=1 |
| GLM-5.2 / 5.1 / 5 | `glm-5.2` / `glm-5.1` / `glm-5` | OpenAI | type=1 |
| Kimi K2.7 / K2.6 / K2.5 | `kimi-k2.7` / `kimi-k2.6` / `kimi-k2.5` | OpenAI | type=1 |
| MiMo-V2.5 / V2.5-Pro / V2-Pro / V2-Omni | `mimo-*` | OpenAI | type=1 |
| Qwen3.5-Plus | `qwen3.5-plus` | OpenAI | type=1 |
| MiniMax M3 / M2.7 / M2.5 | `minimax-m3` / `minimax-m2.7` / `minimax-m2.5` | Anthropic（`/v1/messages`） | type=14 |
| Qwen3.7 Max / Plus / 3.6 Plus | `qwen3.7-max` / `qwen3.7-plus` / `qwen3.6-plus` | Anthropic | type=14 |

### 完整配置（SQLite 直写）

```bash
# === OpenAI 格式渠道（type=1）===
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET models = 'deepseek-v4-flash,deepseek-v4-pro,glm-5.2,glm-5.1,glm-5,kimi-k2.7,kimi-k2.6,kimi-k2.5,mimo-v2.5,mimo-v2.5-pro,mimo-v2-pro,mimo-v2-omni,qwen3.5-plus,hy3-preview' WHERE id = <OpenAI渠道ID>;"

# === Anthropic 格式渠道（type=14）===
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET models = 'minimax-m3,minimax-m2.7,minimax-m2.5,qwen3.7-max,qwen3.7-plus,qwen3.6-plus' WHERE id = <Anthropic渠道ID>;"
```

### 必须禁用 Anthropic 渠道的上游自动同步

NewAPI v1.0.0-rc.14 默认对每个渠道启用 `upstream_model_update_auto_sync_enabled`。启动时会查询上游提供商（OpenCode Go）的 `/v1/models` 端点，把所有可用的模型都匹配到渠道上。这意味着即使你把 DeepSeek 从 Anthropic 渠道的 `models` 字段中移除了，重启后它又会加回来。

```bash
# 禁用 Anthropic 渠道的自动同步
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "UPDATE channels SET settings = '{\"upstream_model_update_auto_sync_enabled\":false}' WHERE id = <Anthropic渠道ID>;"
```

### 如果 abilities 表已空：手动重建

如果禁用了 auto-sync 后 restart，abilities 表可能不会被自动重建。需要手动插入：

```bash
# 查看 abilities 表是否为空
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT COUNT(*) FROM abilities WHERE channel_id IN (3,4);"

# 如果返回 0，手动插入
for model in deepseek-v4-flash deepseek-v4-pro glm-5.2 glm-5.1 glm-5 kimi-k2.7 kimi-k2.6 kimi-k2.5 mimo-v2.5 mimo-v2.5-pro mimo-v2-pro mimo-v2-omni qwen3.5-plus hy3-preview; do
  sudo sqlite3 /home/bluth/new-api/data/one-api.db \
    "INSERT INTO abilities (\"group\", model, channel_id, enabled, priority, weight) VALUES ('default', '$model', 3, 1, 0, 1);"
done
for model in minimax-m3 minimax-m2.7 minimax-m2.5 qwen3.7-max qwen3.7-plus qwen3.6-plus; do
  sudo sqlite3 /home/bluth/new-api/data/one-api.db \
    "INSERT INTO abilities (\"group\", model, channel_id, enabled, priority, weight) VALUES ('default', '$model', 4, 1, 0, 1);"
done
```

### 重启

```bash
# Docker 部署
sudo docker restart new-api

# 本机二进制部署
sudo kill $(pgrep -x new-api | tail -1); sleep 2; /new-api &
```

### 验证

```bash
# 确认 deepseek 只走 OpenAI 渠道
sudo sqlite3 /home/bluth/new-api/data/one-api.db \
  "SELECT channel_id, model FROM abilities WHERE model LIKE '%deepseek%';"
# 预期输出：channel_id 为 OpenAI 渠道的 ID，不应有 Anthropic 渠道

# 功能测试
curl -s --max-time 20 -X POST http://localhost:3000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer sk-<可用token>' \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"hi"}]}'
# 预期返回 choices[0].message.content，非 error
```

---

## 注意事项

1. **每次改库必须重启**——NewAPI 有内存缓存，不重启不生效
2. **SQLite 需要 sudo**——数据库文件属主是 root（Docker 卷映射或本机部署）
3. **Key 不带 sk- 前缀存库**——数据库存 48 位裸字符，给客户时自己加前缀
4. **remain_quota 可以为负**——说明客户已经超用了，改成正数即可恢复
5. **改余额不影响 key**——两个字段独立，客户不需要换 key
6. **⚠️ 上游自动同步陷阱（核心教训）** — NewAPI 对每个渠道默认开启 `upstream_model_update_auto_sync_enabled`。启动时从上游 `/v1/models` 获取全部模型，**无视 `channels.models` 字段**，直接写入 `abilities` 表。这会导致 DeepSeek 模型反复被加回 Anthropic 渠道，即使删了也不行。**Anthropic 格式渠道（type=14）必须彻底关闭 auto-sync**（`{"upstream_model_update_auto_sync_enabled":false}`）。OpenAI 渠道可以保持同步（格式兼容）。每次上游更新模型列表，用户会通知我手动处理——绝不打开 Anthropic 渠道的 auto-sync。
7. **本机二进制部署 vs Docker**：restart 命令不同。本机二进制用 `sudo kill` + 重新启动，Docker 用 `sudo docker restart`。本机部署时 `/new-api` 是单独的可执行文件，不在容器内。

## 参考文档

- [推理强度映射表](references/reasoning-effort-mapping.md) — `max` vs `xhigh` vs `high` 实测对比，OpenCode Go 和 Hermes 的区别
- [成本核算方法论](references/cost-analysis.md) — 输出占比、缓存机制、1亿/10亿成本速算表、官方 vs OpenCode Go 定价对比
- [健康监测部署](references/health-monitoring.md) — cron job 配置、检查项、手动测试命令
- [上游错误诊断](references/upstream-error-diagnosis.md) — 上游错误根因排查：OpenClash Fake-IP 干扰 + DeepSeek 渠道类型不匹配（含 auto-sync 陷阱）
- [Token有效性客户端验证](references/token-validity-check.md) — 没有数据库权限时，从客户端验证Token是否已失效/额度耗尽，区分New API错误与Cloudflare WAF错误
- [参数覆盖 & 模型映射详细说明](references/param-override-and-mapping.md) — models vs model_mapping 区别，param_override/header_override 能力边界，模型身份伪装的可行性
