# 外部凭据轮换与旧凭据失效证据

> 执行日期：`YYYY-MM-DD`  
> 对应 Issue：`#21`  
> 执行人：`<GitHub username / role>`  
> 复核人：`<GitHub username / role>`  
> Gate 状态：`IN PROGRESS | PASSED | FAILED`  
> 安全要求：**本文件不得包含 Access Key、Secret、Token、密码、私钥或可还原凭据的内容。**

## 1. 执行摘要

- 轮换 Provider 数量：`<n>`
- 新凭据验证：`PASS | FAIL | PARTIAL`
- 旧凭据失效验证：`PASS | FAIL | PARTIAL`
- 未完成项：`<无 / 列表>`
- Gate 结论：`GO | NO-GO`

## 2. 凭据盘点

| Provider | 用途 | Secret / 变量名称 | 权限范围 | 旧凭据脱敏标识 | 曾进入 Git 历史 | Owner | 状态 |
|---|---|---|---|---|---|---|---|
| Cloudflare R2 | Electron Preview 对象发布 | `CF_R2_ACCESS_KEY_ID` / `CF_R2_SECRET_ACCESS_KEY` | Bucket `deepagent-releases` 最小对象读写 | `token-id:<...>` / `last4:<....>` | `是 / 否 / 待确认` | `<owner>` | `待轮换` |
| Cloudflare | Account identifier | `CF_ACCOUNT_ID` | 账号标识；仅在账号变化时更新 | `last4:<....>` | `是 / 否 / 待确认` | `<owner>` | `待确认` |
| `<provider>` | `<purpose>` | `<secret name>` | `<scope>` | `<redacted id>` | `<yes/no/unknown>` | `<owner>` | `<status>` |

不得在“脱敏标识”栏填写完整值。

## 3. 新凭据创建与安装

| Provider | 新凭据脱敏 ID | 创建时间（UTC） | 最小权限范围 | GitHub / 平台 Secret 更新时间（UTC） | 结果 |
|---|---|---|---|---|---|
| `<provider>` | `<token id or last4>` | `<timestamp>` | `<scope>` | `<timestamp>` | `PASS / FAIL` |

### 证据说明

- 控制台操作记录：`<脱敏截图或审计日志引用；不得包含 Secret>`
- 密码管理器保存确认：`<仅写已保存，不写位置或值>`
- 异常：`<无 / 描述>`

## 4. 新凭据最小读写验证

验证必须使用隔离测试前缀，不得创建 Tag、Release、Preview/Stable channel 或覆盖正式对象。

| Provider | 隔离资源 / 对象路径 | 上传退出码 | 读回比较 | 删除退出码 | 越权检查 | 时间（UTC） | 结果 |
|---|---|---:|---|---:|---|---|---|
| Cloudflare R2 | `credential-rotation-test/<random-id>` | `<code>` | `MATCH / MISMATCH` | `<code>` | `无额外 Bucket / 账户权限` | `<timestamp>` | `PASS / FAIL` |
| `<provider>` | `<test resource>` | `<code>` | `<result>` | `<code>` | `<result>` | `<timestamp>` | `PASS / FAIL` |

### 验证日志摘要

```text
Provider: <provider>
Operation: upload -> readback -> byte compare -> delete
Result: <PASS/FAIL>
Exit codes: <redacted/non-secret values>
Error code: <none or redacted code>
```

不得粘贴包含 Authorization Header、签名 URL、环境变量值或 Secret 的命令输出。

## 5. 旧凭据撤销

| Provider | 旧凭据脱敏 ID | 撤销时间（UTC） | 撤销位置 | 旧值已从 GitHub / 平台 / 本地移除 | 结果 |
|---|---|---|---|---|---|
| `<provider>` | `<token id or last4>` | `<timestamp>` | `<provider console>` | `YES / NO` | `PASS / FAIL` |

检查范围：

- [ ] Repository Actions Secrets
- [ ] Organization Secrets
- [ ] Environment Secrets
- [ ] Dependabot / Codespaces Secrets
- [ ] 外部部署平台和对象存储
- [ ] 本地 `.env` 和 CI 配置
- [ ] 密码管理器共享项
- [ ] 历史 artifact / 日志引用

## 6. 旧凭据失效验证

仅执行安全的最小只读认证请求；不得使用旧凭据写入、删除或修改资源。

| Provider | 旧凭据脱敏 ID | 请求类型 | HTTP / Provider 错误码 | 预期拒绝 | 时间（UTC） | 结果 |
|---|---|---|---|---|---|---|
| `<provider>` | `<token id or last4>` | `<safe read-only request>` | `<401/403/provider code>` | `YES` | `<timestamp>` | `PASS / FAIL` |

### 脱敏错误证据

```text
Provider: <provider>
Credential: <redacted id only>
Request: <safe read-only operation>
Observed: <authentication failure / permission denied>
Error code: <code>
Timestamp: <UTC timestamp>
```

仅“控制台显示已撤销”不算完成；必须记录旧凭据的实际拒绝结果。

## 7. GitHub 与日志泄漏复核

- [ ] 本文件不含任何 Secret 值
- [ ] Issue #21 不含任何 Secret 值
- [ ] PR / Commit 不含任何 Secret 值
- [ ] Actions 日志不含任何 Secret 值
- [ ] 测试对象已删除
- [ ] 新凭据未进入命令历史或可公开 artifact
- [ ] 旧凭据值未被复制到新文档或聊天

复核方法：`<人工复核 / secret scanner / 两者>`

## 8. 未完成项与异常

| 项目 | 原因 | 风险 | Owner | 下一动作 | 截止条件 |
|---|---|---|---|---|---|
| `<item>` | `<reason>` | `<risk>` | `<owner>` | `<action>` | `<condition>` |

无未完成项时写：`无`。

## 9. Gate 判定

- [ ] 所有已知外部凭据已盘点
- [ ] 新凭据遵循最小权限
- [ ] GitHub / 外部平台 Secret 已更新
- [ ] 新凭据最小读写验证成功
- [ ] 旧凭据已撤销
- [ ] 旧凭据实际验证失败
- [ ] 脱敏证据已进入远程仓库
- [ ] 无 Secret 值进入 GitHub、日志或文档

**最终判定：** `PASSED | FAILED`

**判定依据：** `<简要说明>`

**下一唯一任务：** Gate 为 `PASSED` 后，开始清理 Git 历史中的有效秘密，并对全部 Git refs 重新扫描；Gate 未通过时不得开始历史重写。
