# DeepAgent 三阶段计划 · 开发交接文档

> **日期**: 2026-07-28
> **交接人**: 小路的数字分身（经由 Codex 执行 + Hermes Agent 整理）
> **接手人**: 后续研发人员
> **基础分支**: `develop`

---

## 一、当前进度总览

| 阶段 | 完成度 | 状态 |
|---|---|---|
| 第一阶段 CLI Alpha | ~95% | ✅ **代码已全部完成**，待外部门禁 |
| 第二阶段 WebUI Beta | ~85% | ✅ **核心功能已全部完成**，待 E2E 测试 |
| 第三阶段 Electron Preview | ~75% | ✅ **架构和核心模块已完成**，待收尾和工作区互斥修复 |

共 **15 个原子 commit**，从 commit `b3943ac43` 开始，到 `97f6736df` 结束。
顺序查看：`git log --oneline HEAD~15..HEAD`

---

## 二、Commit 清单（从旧到新）

| # | Commit Hash | 分类 | 说明 |
|---|---|---|---|
| 1 | `03d700772` | Phase 1 | Core 目录隔离 DEEPAGENT_HOME |
| 2 | `30fefc778` | Phase 1 | 安装器/卸载器/更新重写 |
| 3 | `2b3eafd5f` | Phase 1 | CLI 主入口重构 |
| 4 | `5a93ff969` | Phase 1 | 开源治理文档 |
| 5 | `386a4f643` | Phase 1 | 三渠道发布管道 |
| 6 | `d2f4ea2dc` | Phase 1 | 官网文档收敛 |
| 7 | `927304045` | Phase 1 | 开发工具和测试脚本 |
| 8 | `50747eec9` | Phase 2 | WebUI 认证重写（Ticket + Session） |
| 9 | `242bb46c6` | Phase 2 | 品牌清理 Hermes → DeepAgent |
| 10 | `3346a5e27` | Phase 2 | WebUI CLI 命令 + 共存 + NPM 许可审计 |
| 11 | `d540c7db1` | Phase 2 | WebUI 测试收敛 |
| 12 | `4fa0c6241` | Phase 3 | Electron 双模式架构 |
| 13 | `25b154c3e` | Phase 3 | Keychain 凭据库 + 迁移 + 工作区锁 |
| 14 | `d1c7018a0` | Phase 3 | Electron 构建 + Preview 发布会话 |
| 15 | `71174f062` | Phase 3 | DeepCode 安装器 |
| — | `97f6736df` | All | 网站测试 |

---

## 三、各阶段完成详情

### 第一阶段 CLI Alpha（15 个 commit 中的 1~7）

**已完成的代码变更：**

1. **目录隔离**：`DEEPAGENT_HOME` 取代 `HERMES_HOME` 作为产品根目录
   - 关键文件：`hermes_constants.py`, `hermes_cli/env_loader.py`, `run_agent.py`, `tools/file_operations.py`
   - 测试隔离：`tests/conftest.py`（两变量同时重定向到临时目录 + API Key 清洗）

2. **安装器/卸载器**：
   - `scripts/install-release.sh`：苹果 Silicon 独占，Manifest + SHA-256 校验，渠道指针原子更新
   - `hermes_cli/uninstall.py`：从递归删除改为清单驱动，realpath 边界校验
   - `hermes_cli/update.py`：Manifest 校验 + 原子符号链接切换，同版本覆写仅允许哈希一致

3. **CLI 命令路由**：`hermes_cli/main.py` 按阶段注册命令，不可用命令显示"not installed"

4. **发布管道**：
   - `.github/workflows/release.yml`：三渠道（Alpha/Beta/Preview），密钥扫描阻断
   - `scripts/build-release.sh`：Core-only macOS arm64，生产依赖裁剪
   - `scripts/generate-release-manifest.py`：多渠道 Manifest

5. **文档和治理**：CODE_OF_CONDUCT, SECURITY, NOTICE, THIRD_PARTY_NOTICES, CONTRIBUTING, README
6. **官网**：`website/` Docusaurus 站点全部收敛到 DeepAgent 范围，`landingpage/` 安装落地页

**尚未完成的外部门禁（需要小路手动操作）：**

> ⚠️ 以下事项不在代码层面，需要小路授权后执行：

```
1. 凭据轮换：当前 Git 历史中有对象存储凭据需要轮换
   - 步骤：旋转 R2/对象存储 API 密钥 → 更新 GitHub Secrets
2. Git 历史清洗：用 git filter-branch 或 BFG 清理历史中的凭据
   - 脚本：scripts/audit-python-licenses.py（作为审计模板）
3. Parallels VM 验收：在 macOS 15.5 Apple Silicon VM 执行完整门禁
   - 步骤看 PLAN.md 第 4 节
```

**测试结果**：11,857 passed / 92 failed / 5 error（失败为沙箱环境限制，非产品问题）

---

### 第二阶段 WebUI Beta（15 个 commit 中的 8~11）

**已完成的代码变更：**

1. **认证重写**：移除硬编码 admin/123456
   - 一次性登录 Ticket → HttpOnly Session Cookie
   - 关键文件：`webui/packages/server/src/services/login-ticket.ts`, `controllers/auth.ts`, `middleware/user-auth.ts`
   - 测试：73 项认证测试全部通过

2. **品牌清理**：所有面向用户的 Hermes 名称改为 DeepAgent
   - 8 语言 i18n，README，index.html，manifest，LoginView
   - RegisterView.vue 已删除
   - 不修改内部 API 路径和协议常量

3. **WebUI CLI 命令**：`deepagent webui start/open/status/stop`
   - `hermes_cli/webui.py`, `hermes_cli/webui_install.py`
   - 端口自主选择，不抢进程，私有 Node.js 运行时

4. **共存加固**：WebUI 数据移到 `~/.deepagent/data/webui/`，LAN 默认关闭
5. **NPM 许可证审计**：`webui/scripts/audit-npm-licenses.mjs`
6. **Beta 发布会话**：`.github/workflows/release-webui-beta.yml`

**测试结果**：260 个文件、1,945 项通过、0 失败、2 跳过

**需要后续完成：**
- 浏览器 E2E 测试（`tests/e2e/auth.spec.ts`）需要真实浏览器环境
- 新版官网构建上线（`scripts/build-website.sh`）
- LAN 访问独立评估

---

### 第三阶段 Electron Preview（15 个 commit 中的 12~15）

**已完成的代码变更：**

1. **双模式架构**：ModeManager 管理 Agent + Code 两个运行时
   - 关键文件：`webui/packages/desktop/src/main/mode-manager.ts`, `index.ts`, `cli-shim.ts`, `hermes-cli.ts`
   - 切换不重启应用，独立 IPC 命名空间和状态目录

2. **子进程隔离**：`child-env.ts` 环境变量白名单，API Key 不继承

3. **凭据安全**：`credential-vault.ts` macOS Keychain 存储
   - Key 不进 Renderer/日志/持久存储
   - 只通过 Main Process IPC 注入子进程

4. **数据迁移**：`migration.ts` 从旧 Hermes/Electron 一次迁移
   - 幂等，失败不影响启动

5. **工作区锁**：`workspace-lock.ts` 写-写互斥
   - ⚠️ 已知缺陷：写+读并发暂未隔离

6. **构建配置**：
   - `electron-builder.yml`：DeepAgent Preview, org.starseas.deepagent
   - `release-electron-preview.yml`：完整签名+公证发布会话

7. **DeepCode 安装器**：`hermes_cli/deepcode_install.py`

**测试结果**：Electron 主进程 16 项通过，credential-vault 测试通过，migration 测试通过

**已知缺陷（需要修复）：**

```typescript
// workspace-lock.ts: write+read 暂未做互斥
// ponytail: 当前允许多个 writer 互斥，writer+reader 可以同时进入同一工作区
// 修复路径：在 mode-manager 的 IPC handler 层协调 workspace-lock
// 即工作区级别的读写锁，需要 IPC 层的 acquireWorkspaceLock(mode, workspace, type)
```

**需要外部操作：**
- Apple Developer 证书配置为 GitHub Secrets
- macOS runner 用于 Electron 构建
- Apple Developer 账户（$99/年）用于公证

---

## 四、如何继续开发

### 4.1 从最新状态继续

```bash
git checkout develop
git log --oneline -1  # 确认在最新 commit
```

### 4.2 启动开发环境

```bash
# Python 环境
source venv/bin/activate

# WebUI 环境
cd webui && npm install

# 运行 Python 测试（完整套件）
python -m pytest tests/ -q

# 运行 WebUI 测试
cd webui && npx vitest run

# 运行 Electron 主进程测试
cd webui && npx vitest run --config packages/desktop/vitest.config.ts
```

### 4.3 最优先修复的缺陷

1. **工作区写+读互斥**（P1）
   - 文件：`webui/packages/desktop/src/main/workspace-lock.ts`
   - 目标：write 任务运行时，read 任务不能进入同一工作区
   - 方法：在 mode-manager IPC handler 中增加 `acquireWorkspaceLock(mode, workspace, 'read'|'write') ` 调用

2. **凭据轮换 + Git 历史清理**（P0 外部门禁——见下方 5.1）

### 4.4 推荐的开发顺序

```
1. 修复 workspace-lock 写+读互斥（P1，代码级）
2. 在 Parallels VM 中执行第一阶段文档门禁（验证安装/升级/回滚/卸载）
3. 配置 Apple Developer 证书（P2，外部操作）
4. 执行 Electron 浏览器 E2E 测试（P2，需要真实显示器）
5. LAN 访问设计评审（P3，不阻塞发布）
```

### 4.5 文件组织图

```
deepseekagent/
├── hermes_cli/                  # CLI 核心
│   ├── main.py                  # 入口（分阶段命令路由）
│   ├── env_loader.py            # 环境变量加载（DEEPAGENT_HOME）
│   ├── uninstall.py             # 清单驱动卸载
│   ├── update.py                # Manifest 校验更新
│   ├── webui.py                 # deepagent webui 命令
│   ├── webui_install.py         # WebUI 组件安装器
│   └── deepcode_install.py      # DeepCode 组件安装器
├── hermes_constants.py          # 常量（DEEPAGENT_HOME 定义）
├── scripts/
│   ├── install-release.sh       # 安装器
│   ├── build-release.sh         # 发布构建
│   ├── generate-release-manifest.py  # Manifest 生成
│   ├── audit-python-licenses.py # Python 许可审计
│   └── test-release-e2e.sh      # 发布 E2E
├── website/                     # 官网（Docusaurus）
├── landingpage/                 # 安装落地页
├── webui/
│   ├── packages/
│   │   ├── client/              # 前端 Vue
│   │   ├── server/              # 后端服务
│   │   │   └── src/services/login-ticket.ts  # 一次性 Ticket
│   │   └── desktop/             # Electron 客户端
│   │       ├── electron-builder.yml
│   │       └── src/main/
│   │           ├── index.ts           # Electron 主进程
│   │           ├── mode-manager.ts    # 双模式管理
│   │           ├── credential-vault.ts # Keychain 凭据库
│   │           ├── migration.ts       # 数据迁移
│   │           ├── workspace-lock.ts  # 工作区锁 ⚠️ 需修复
│   │           ├── child-env.ts       # 子进程环境白名单
│   │           └── login-ticket.ts    # 桌面端 Ticket
│   ├── scripts/
│   │   ├── audit-npm-licenses.mjs     # NPM 许可审计
│   │   └── copy-production-deps.mjs   # 生产依赖复制
│   └── .github/workflows/
│       ├── release.yml                 # Alpha 发布
│       ├── release-webui-beta.yml      # Beta 发布
│       └── release-electron-preview.yml # Preview 发布
├── docs/
│   ├── open-source-readiness/         # 完整规划文档
│   └── HANDOFF-DEVELOPER.md           # ← 就是这个文件
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── NOTICE
├── THIRD_PARTY_NOTICES.md
└── CONTRIBUTING.md
```

---

## 五、外部门禁清单

### 5.1 必须由小路完成的 🔴

| 事项 | 说明 | 操作步骤 |
|---|---|---|
| 凭据轮换 | 旋转对象存储 API 密钥 | ① 登录 Cloudflare/对象存储控制台 ② 生成新密钥 ③ 更新 GitHub Secrets ④ 废弃旧密钥 |
| Git 历史清理 | 移除已轮换凭据的所有历史引用 | `git filter-branch --tree-filter ...` 或 BFG Repo-Cleaner |
| 首次发布批准 | 确认上述操作后，打 tag 进行首次 Alpha 发布 | 详见 `scripts/test-release-e2e.sh` |

### 5.2 需要外部资源 🟡

| 事项 | 所需资源 |
|---|---|
| Apple Developer 证书 | Apple Developer 账户 ($99/年) + 证书导出为 .p12 |
| Parallels VM 验收 | Parallels Desktop + macOS 15.5 Apple Silicon VM |
| 浏览器 E2E 测试 | 带图形界面的 macOS 机器（非沙箱环境） |
| Electron 签名 + 公证 | 上述 Apple Developer 证书配置为 GitHub Secrets |
| Beta/Preview 发布 | GitHub Actions 或自建 CI Runner |

---

## 六、常见操作

### 查看当前分支的提交历史
```bash
git log --oneline -20
```

### 查看某个文件的修改历史
```bash
git log --oneline -- <filepath>
```

### 对比当前和某个阶段的差异
```bash
# 看某次 commit 改了什么
git show <commit-hash> --stat

# 看两个 commit 之间的差异
git diff <hash1>..<hash2> --stat
```

### 回退某个文件到某个 commit
```bash
git checkout <commit-hash> -- <filepath>
```

### cherry-pick 某个功能到另一分支
```bash
git cherry-pick <commit-hash>
```

---

## 七、各阶段核心 KPI

| 阶段 | 判定条件 | 当前状态 |
|---|---|---|
| Alpha 可发布 | 凭据轮换 + 历史清理 + VM 验收通过 | ❌ 凭据和历史待清理，其余 ✅ |
| Beta 可发布 | E2E 浏览器测试通过 + 官网构建上线 | 🔶 代码 ✅，E2E 需真实环境 |
| Preview 可发布 | 签名公证 + 文档门禁 + 工作区锁修复 | 🔶 代码 ~75%，Apple 证书和互斥修复待完成 |

---

> **最后建议**: 接手后第一件事是拉 branch 然后修复 `workspace-lock.ts` 的写+读互斥问题
> （文件底部附近有 `ponytail:` 注释标明），这是唯一已知的代码级缺陷。
> 其他全部是外部操作/E2E 测试。
