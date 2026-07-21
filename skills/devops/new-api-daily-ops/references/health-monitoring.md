# NewAPI 健康监测（Cron Job）

## 部署位置

- 脚本：`~/.hermes/scripts/newapi-health-check.py`
- Cron job ID：`9355ec259181`
- 频率：每 5 分钟 (`*/5 * * * *`)
- 模式：`no_agent=True`（脚本输出直发飞书）
- 投递：飞书 Home 频道

## 检查项

1. Docker 容器状态（`new-api` 是否 running）
2. API 状态端点（`/api/status` 返回 200）
3. 模型实际推理（`deepseek-v4-flash` 完整调用返回 choices）

## 行为

- **三项全通** → 静默，不发消息
- **任何一项异常** → 脚本输出报警文本 → cron 直发飞书

## 重新创建命令

```bash
# 如果 cron job 丢失，用以下命令重建：
cronjob create \
  --schedule "*/5 * * * *" \
  --script "newapi-health-check.py" \
  --no_agent \
  --deliver "feishu:oc_0ce0dea33926c6678331d53eac056eb6" \
  --profile "cto" \
  --name "NewAPI 健康监测"
```

## 手动测试

```bash
# 正常时应该无输出（静默）
python3 ~/.hermes/scripts/newapi-health-check.py

# 模拟故障：停止容器后运行，应有报警输出
sudo docker stop new-api
python3 ~/.hermes/scripts/newapi-health-check.py
sudo docker start new-api
```
