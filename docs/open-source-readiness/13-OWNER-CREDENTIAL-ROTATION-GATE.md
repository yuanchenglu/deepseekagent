# Owner Gate：外部凭据轮换与旧凭据失效确认

> 状态：**BLOCKED — 需要仓库 Owner / 外部平台管理员执行**  
> 日期：2026-07-29  
> 前置任务：双 Runtime 同 Workspace 并发与故障 E2E 已完成  
> 后继任务：Git 历史有效秘密清理与全 refs 重扫

## 1. Gate 目标

在不把任何凭据值写入 GitHub、日志、Issue、PR 或聊天的前提下：

1. 盘点所有曾进入代码、配置、日志、制品或 Git 历史的外部凭据；
2. 创建权限最小化的新凭据；
3. 更新 GitHub Actions / 外部平台 Secret；
4. 验证新凭据可完成最小读写闭环；
5. 撤销旧凭据；
6. 证明旧凭据已失效；
7. 保存脱敏证据。

只有以上全部完成，Gate 才能关闭。

## 2. 当前已确认的发布 Secret 名称

Electron Preview 发布工作流使用：

- `CF_R2_ACCESS_KEY_ID`
- `CF_R2_SECRET_ACCESS_KEY`
- `CF_ACCOUNT_ID`
- GitHub 提供的 `GITHUB_TOKEN`（无需人工创建长期 Token）

R2 目标 Bucket：`deepagent-releases`。

以上清单不是对整个仓库和所有第三方平台的穷举。Owner 在轮换前必须再次审计：

- 仓库与组织 Actions Secrets；
- Environments Secrets；
- Dependabot / Codespaces Secrets；
- Cloudflare R2 / DNS / Pages；
- GitHub Releases、Pages、Package Registry；
- 模型 Provider、遥测、错误上报、邮件、对象存储和其他服务账号；
- 本地 `.env`、CI 日志、历史 artifact 和 Git 全 refs 中出现过的凭据。

## 3. Owner 输入

Owner 需要具备：

- `yuanchenglu/deepseekagent` 的仓库或组织 Secrets 管理权限；
- Cloudflare 账号和 R2 API Token 管理权限；
- 其他被盘点外部服务的管理员权限；
- 能在安全本地环境验证旧/新凭据的终端；
- 不向仓库或聊天粘贴明文凭据的操作纪律。

## 4. 执行步骤

### 4.1 盘点

为每个凭据记录脱敏条目：

| 字段 | 要求 |
|---|---|
| Provider | 平台/服务名称 |
| 用途 | 发布、读、写、模型调用等 |
| Secret 名称 | GitHub Secret 或本地变量名 |
| 权限范围 | Bucket、仓库、环境、API Scope |
| 旧凭据标识 | 仅保留平台显示的末 4 位或内部 ID |
| 是否曾进入 Git 历史 | 是/否/待确认 |
| Owner | 执行人 |

不得记录 Secret 值。

### 4.2 创建新凭据

以 R2 为例：

1. 创建新的 R2 API Token；
2. 权限限制到 `deepagent-releases` 所需的最小对象读写范围；
3. 不授予账户级无关管理权限；
4. 保存新 Access Key ID / Secret Access Key 到密码管理器；
5. 记录 Token ID 和创建时间，不记录 Secret 值。

其他 Provider 使用相同的最小权限原则。

### 4.3 更新 GitHub Secrets

在仓库或组织设置中更新对应 Secret：

- `CF_R2_ACCESS_KEY_ID`
- `CF_R2_SECRET_ACCESS_KEY`
- `CF_ACCOUNT_ID`（仅当账号或配置需要变更）

不得通过 Commit、PR、Issue、日志或 workflow 默认值传递凭据。

### 4.4 验证新凭据

执行一个不公开发布的最小验证：

1. 向隔离测试前缀上传一个随机测试对象；
2. 读回并进行字节级比较；
3. 删除测试对象；
4. 确认无多余 Bucket / 账户权限；
5. 记录命令退出码、对象路径、时间和脱敏 Token ID；
6. 对其他 Provider 执行等价的最小权限验证。

不得创建正式 Tag、公开 Release、Stable/Preview channel 或不可逆公开内容。

### 4.5 撤销旧凭据

1. 在 Provider 控制台撤销旧 Token / Key；
2. 删除仓库、组织、环境和本地环境中的旧值；
3. 检查缓存、CI 变量、密码管理器共享项和部署平台；
4. 确认不存在仍引用旧凭据的自动化。

### 4.6 验证旧凭据失效

在隔离安全环境中使用旧凭据执行最小只读请求：

- 预期结果：认证失败或权限拒绝；
- 不允许使用旧凭据执行写入；
- 保存脱敏错误码、时间、Provider 和旧凭据末 4 位；
- 不保存或上传旧凭据值。

仅“已点击撤销”不能替代失效验证。

## 5. Gate 证据

完成后需要向仓库提交一份不含秘密的证据记录，至少包含：

- Provider 和用途；
- 新凭据创建时间及脱敏 ID；
- GitHub Secret 更新时间；
- 新凭据最小读写验证结果；
- 旧凭据撤销时间；
- 旧凭据认证失败的脱敏证据；
- 执行人和复核人；
- 未完成或异常项。

建议文件：

`docs/open-source-readiness/evidence/CREDENTIAL-ROTATION-YYYY-MM-DD.md`

## 6. 完成判定

以下条件全部满足才可将 Gate 标记为完成：

- 所有已知外部凭据已盘点；
- 新凭据遵循最小权限；
- GitHub / 外部平台 Secret 已更新；
- 新凭据验证成功；
- 旧凭据已撤销；
- 旧凭据验证失败；
- 脱敏证据已进入远程仓库；
- 没有 Secret 值出现在 GitHub、日志或文档。

完成后唯一下一任务是：

> **清理 Git 历史中的有效秘密，并对全部 Git refs 重新扫描。**
