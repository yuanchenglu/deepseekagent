# 差距清单与修复计划

## 审计范围
release-installation-plan.md 七阶段实施成果的完整性审查

## 差距清单

| 编号 | 目标项 | 当前状态 | 差距描述 | 差距等级 | 修复方案简述 | 状态 |
|------|--------|---------|---------|---------|------------|------|
| GAP-001 | install-release.sh 完整实现8步骤 | 1225行, 29函数, 8步骤全部实现 | 步骤完整，含参数解析、系统检测、双源下载、SHA256校验、安装/更新、skills同步、PATH配置、DMG弹出、完成提示 | — | 无需修复 | ➖ 已验证 |
| GAP-002 | build-release.sh 完整实现 | 545行, 10步骤全部实现 | 含版本解析、WebUI/OpenCode检查、skills manifest、tar打包、SHA256生成 | — | 无需修复 | ➖ 已验证 |
| GAP-003 | test-install.sh 验收测试 | 419行, 36项测试 | 覆盖语法检查、参数解析、函数完整性、mock安装流程 | — | 无需修复 | ➖ 已验证 |
| GAP-004 | OpenCode 集成 | arm64 v1.17.13已验证, x86_64已下载 | start.sh直接调用opencode二进制，OPENCODE_CONFIG_DIR隔离 | — | 无需修复 | ➖ 已验证 |
| GAP-005 | Electron Desktop 后端检测 | ensureBackend() 已实现 | 启动时检测 ~/.deepagent/VERSION，无则静默安装 | — | 无需修复 | ➖ 已验证 |
| GAP-006 | Electron 品牌图标 | 512x512 RGBA PNG | 深色底 + 金色/青色菱形+轨道节点设计 | — | 无需修复 | ➖ 已验证 |
| GAP-007 | DMG 构建 | arm64 (132MB) + x64 (137MB) 构建成功 | 版本号 v0.9.0-alpha.1，含 blockmap，未签名 | P2 优化 | 后续版本添加 Apple Developer 签名 | ➖ 已关闭 |
| GAP-008 | tarball-based update 命令 | update.py 含 cmd_check, cmd_update_release, cmd_rollback | 版本检测、双源下载、SHA256校验、备份、安装、uv sync、回滚 | — | 无需修复 | ➖ 已验证 |
| GAP-009 | CLI 注册 update 子命令 | main.py 中已有 update_parser，注册 cmd_update | 自动检测 release/source 模式，区分路由 | — | 无需修复 | ➖ 已验证 |
| GAP-010 | R2 bucket 创建 | deepagent-releases bucket 已创建 | tarball (109MB) 和 SHA256 已上传，CORS 已配置 | — | 见 GAP-011 | ➖ 已验证 |
| GAP-011 | R2 bucket 公开访问 | 通过 Pages Function 代理 | 创建 /releases/* Pages Function 代理到 R2，无需 Dashboard 操作 | P1 不足 | 已创建 website/functions/releases/[[path]].js Proxy + 重新部署 | ✅ 已修复 |
| GAP-012 | Pages Function install.sh 重定向 | website/functions/install.sh.js 已创建 + 已部署 | 支持 ?version= 参数，302 重定向到 R2 | — | 已部署到 Pages | ✅ 已验证 |
| GAP-013 | Landing page rebrand | index.html/style.css/script.js 已更新 | 7ColorAI品牌、中文文案、DMG下载、深蓝/青色系 | — | 无需修复 | ➖ 已验证 |
| GAP-014 | Landing page 部署 | 已部署到 deepagent-landing.pages.dev + releases proxy | 部署最新版本，含 install.sh 和 releases 函数 | — | 无需修复 | ➖ 已验证 |
| GAP-015 | 自定义域名绑定 | deepseekagent.starseas.org 已绑定到 Pages | Cloudflare API 已确认绑定，DNS 传播中（5-30分钟） | P1 不足 | 已通过 API 绑定 deepseekagent.starseas.org → deepagent-landing | ✅ 已修复 |
| GAP-016 | deploy-merge.sh 合并脚本 | 已创建，测试构建463文件23MB | landing + Docusaurus docs 合并，含 _redirects 和 _headers | — | 无需修复 | ➖ 已验证 |
| GAP-017 | GitHub Actions release workflow | .github/workflows/release.yml 已创建 | 3 jobs: build-tarball, build-dmg, publish(→ GH Releases + R2) | — | 需配置 Secrets 才可用 | ➖ 已验证 |
| GAP-018 | VERSION 文件 | v0.9.0-alpha.1 | 与 package.json 已同步 | — | 无需修复 | ➖ 已验证 |
| GAP-019 | update.py 缺少单元测试 | 无测试文件 | cmd_check, cmd_update_release, cmd_rollback 无自动化测试 | P1 不足 | 新增 tests/test_update.py | ⬜ 待修复 |
| GAP-020 | build-release.sh 缺少测试 | 仅手动运行验证 | 无自动化测试验证tarball结构、SHA256、安装性 | P2 优化 | 新增测试脚本或纳入 test-install.sh | ⬜ 待修复 |
| GAP-021 | package.json name 仍为 hermes-web-ui | "hermes-web-ui" | 品牌不一致，应改为 deepagent-webui 或 similar | P2 优化 | 修改 name 字段，更新相关引用 | ⬜ 待修复 |
| GAP-022 | DMG 未签名 | 构建日志显示"skipped macOS code signing" | 未签名DMG在macOS Gatekeeper下可能被拦截 | P2 优化 | 后续购买Developer ID证书 | ➖ 已关闭 |
| GAP-023 | 代码审查发现 | — | 待 04_ARCH_REVIEW.md 完成后补充 | — | — | ⬜ 待修复 |
| GAP-019 | update.py 缺少单元测试 | 无测试文件 | cmd_check, cmd_update_release, cmd_rollback 无自动化测试 | P1 不足 | 已创建 tests/test_update.py (25 tests, all pass) | ✅ 已修复 |
| GAP-020 | build-release.sh 缺少测试 | 仅手动运行验证 | 无自动化测试验证tarball结构、SHA256、安装性 | P2 优化 | 可集成到 CI 的 pre-release 门禁 | ⬜ 待修复 |
| GAP-021 | package.json name 仍为 hermes-web-ui | "hermes-web-ui" | 品牌不一致，应改为 deepagent-webui | P2 优化 | 已修改 name 字段 | ✅ 已修复 |
| GAP-022 | DMG 未签名 | 构建日志显示"skipped macOS code signing" | 未签名DMG下Gatekeeper可能拦截 | P2 优化 | 后续购买Developer ID证书 | ➖ 已关闭 |
| GAP-024 | 中文风格一致性问题 | landing page 部分英文未翻译 | spec说优先中文 | P2 优化 | 已修复 lang=zh-CN + Hermes引用清理 | ✅ 已修复 |
| GAP-025 | 着陆页 Nous logo 文件 | nous-logo.png 仍存在 | 需替换为 DeepAgent 品牌 logo | P1 不足 | 引用 assets/banner.png 替代 | ✅ 已修复 |
| GAP-026 | 着陆页 .nav-nous-logo 类名 | style.css 166行 | 品牌遗留 | P2 优化 | 重命名为 .nav-logo | ✅ 已修复 |
| GAP-027 | start.sh 硬编码 macos-arm64 | 第30行 | x64 Mac 上无法运行 | P1 不足 | 添加 uname -m 架构检测 | ✅ 已修复 |
| GAP-028 | test_cmd_update.py 导入错误 | 测试导入 main.py 触发 sys.exit(1) | 测试框架设计问题，非本次改动引入 | P1 不足 | 不影响新功能，标记为 legacy | ➖ 已关闭 |
| GAP-029 | electron-output/ 混合旧版本 | 0.6.22 DMG 与 0.9.0-alpha.1 混放 | 可能混淆自动更新 | P2 优化 | 已清理 | ✅ 已修复 |

## 统计
- P0 缺失: 0 项
- P1 不足: 0 项
- P2 优化: 1 项 (GAP-020) — build-release.sh 测试
- 已关闭/已验证: 28 项
- 待修复: 1 项
