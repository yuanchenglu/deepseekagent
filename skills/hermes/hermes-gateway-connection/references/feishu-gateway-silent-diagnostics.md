# Feishu Gateway Silent Failure — 完整诊断重现步骤

源自真实故障：飞书发消息后 Hermes 完全无响应，Gateway 运行中但 `No messaging platforms enabled`。

## 诊断步骤（完整重现）

### Step 1: 检查网关状态

```bash
hermes gateway status
```
→ 服务已加载，PID 存在

### Step 2: 查看配置摘要

```bash
hermes config
```
→ Messaging Platforms 无飞书 — 平台适配器未加载

### Step 3: 检查网关日志（关键证据）

```bash
grep -E "platform|feishu|enabled|connect" ~/.hermes/logs/gateway.log | tail -30
```

故障信号：
```
WARNING gateway.run: No messaging platforms enabled.
```

正常信号（对比旧日志）：
```
INFO gateway.run: Connecting to feishu...
INFO hermes_plugins.feishu_platform.adapter: [Feishu] Connected
INFO gateway.run: ✓ feishu connected
```

### Step 4: 检查 .env 凭据（根因）

```bash
grep -i "FEISHU\|LARK" ~/.hermes/.env
```
→ 空结果 = 凭据丢失

### Step 5: 确认飞书插件代码仍存在

```bash
find ~/.hermes/hermes-agent -path "*/feishu*" -name "*.py" | head -5
```
→ 插件路径：`plugins/platforms/feishu/`

插件要求（`plugin.yaml`）：
- 必须：`FEISHU_APP_ID`, `FEISHU_APP_SECRET`
- 建议：`FEISHU_DOMAIN=feishu`, `FEISHU_ALLOW_ALL_USERS=true`

### Step 6: 检查用户配对

```bash
cat ~/.hermes/pairing/feishu-approved.json
```

### Step 7: 检查 Python 依赖

```bash
cd ~/.hermes/hermes-agent && source venv/bin/activate && python3 -c "import lark_oapi; print('OK')"
```

## 恢复步骤

```bash
# 1. 写入凭据
echo 'FEISHU_APP_ID=cli_xxx' >> ~/.hermes/.env
echo 'FEISHU_APP_SECRET=***' >> ~/.hermes/.env

# 2. 重启网关
hermes gateway restart

# 3. 验证
sleep 5 && tail -10 ~/.hermes/logs/gateway.log
```

恢复后的日志：
```
Connecting to feishu...
[Feishu] Connected in websocket mode (feishu)
✓ feishu connected
Gateway running with 1 platform(s)
```

## 关键洞察

1. **"No messaging platforms enabled" + 网关在运行 ≈ .env 凭据丢失**
2. `required_env` 不满足 → 插件静默不加载，无报错
3. 必须重启网关才能让 .env 变更生效
4. `.env` 可能在更新/迁移中被重建或覆盖
