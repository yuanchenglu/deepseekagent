# Cloudflare R2 凭据轮换分阶段自动验证证据

> Provider：Cloudflare R2  
> Bucket：`deepagent-releases`  
> Account ID 脱敏标识：`last4:160a`  
> Secret 值：**未记录**

## SEC-004：新凭据最小读写闭环

> 执行开始（UTC）：`2026-08-03T07:29:39Z`  
> 执行完成（UTC）：`2026-08-03T07:30:22Z`  
> 新 Access Key 脱敏标识：`last4:3c63`

| 检查项 | 结果 |
|---|---|
| 新凭据隔离对象上传 | PASS |
| 新凭据读回 | PASS |
| 字节级比较 | PASS |
| 隔离对象删除 | PASS |
| Tag / Release / Channel 变更 | 未执行 |

## SEC-006：旧凭据失效验证

> 执行开始（UTC）：`2026-08-03T07:30:51Z`  
> 执行完成（UTC）：`2026-08-03T07:30:52Z`  
> 旧 Access Key 脱敏标识：`last4:3874`

| 检查项 | 结果 |
|---|---|
| 旧凭据安全只读请求 | DENIED（退出码 `255`） |
| 旧凭据写入操作 | 未执行 |
| Tag / Release / Channel 变更 | 未执行 |

## 人工复核清单

- [x] 新 Token 的平台权限范围仅覆盖所需 Bucket / 对象操作（bucket-scoped，仅 deepagent-releases）
- [x] Repository Secrets 已盘点（4 个：CF_ACCOUNT_ID, CF_R2_ACCESS_KEY_ID, CF_R2_SECRET_ACCESS_KEY, CLOUDFLARE_API_TOKEN）
- [x] Organization / Environment / Dependabot Secrets 已盘点（均不存在）
- [x] 其他 Provider 凭据：本仓库发布管线仅使用 Cloudflare R2 + Pages，无其他 Provider
- [x] 本地 shell history 不含旧值（HISTFILE=/dev/null，环境变量引用，未写文件）
- [x] CI 日志不含 Secret 值（GitHub Actions 日志自动掩码 Secret）
- [x] 本文件及相关 PR、Issue、Actions 日志不含任何 Secret 值

## SEC-005 撤销记录

- 旧 R2 Account Token ID（脱敏）：`last4:3874`
- 撤销方式：Cloudflare API DELETE /accounts/{account_id}/tokens/{token_id}
- 撤销时间（UTC）：2026-08-03T07:30Z
- 撤销后确认：Account tokens 列表为空

## SEC-003 Secret 更新记录

| Secret | 更新时间(UTC) | 说明 |
|---|---|---|
| CF_ACCOUNT_ID | 2026-08-03T06:21:21Z | 值未变（Account ID 非凭据） |
| CF_R2_ACCESS_KEY_ID | 2026-08-03T07:29:10Z | 新最小权限 Token |
| CF_R2_SECRET_ACCESS_KEY | 2026-08-03T07:29:20Z | 新最小权限 Token |
| CLOUDFLARE_API_TOKEN | 2026-08-03T06:21:45Z | 新建（之前缺失） |
