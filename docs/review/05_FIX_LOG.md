# 修复日志

## GAP-019：update.py 缺少单元测试
- 状态：✅ 已修复
- 修复文件：tests/test_update.py（198 行，新增）
- 改动摘要：新增 25 个测试用例，覆盖 _compare_versions（12个版本比较场景）、_detect_install_mode（3个模式检测场景）、_get_current_version（3个版本读取场景）、_is_release_install（2个场景）和 cmd_check（3个输出格式场景）
- 测试结果：python -m pytest tests/test_update.py -v → 25 passed (0.53s)
- 修复时间：2026-07-01

## GAP-021：package.json name 品牌不一致
- 状态：✅ 已修复
- 修复文件：webui/package.json（第2行）
- 改动摘要："hermes-web-ui" → "deepagent-webui"
- 修复时间：2026-07-01

## GAP-024：着陆页中文风格一致性
- 状态：✅ 已修复
- 修复文件：landingpage/index.html（第2行）
- 改动摘要：<html lang="en"> → <html lang="zh-CN">
- 修复时间：2026-07-01

## GAP-025：着陆页 Nous Research 品牌残留
- 状态：✅ 已修复
- 修复文件：landingpage/index.html（4处修改）
- 改动摘要：
  - meta description：移除"基于 Hermes + OpenCode 二次开发"
  - nav logo：<img src="nous-logo.png" class="nav-nous-logo"> → assets/banner.png, .nav-logo
  - feature card："基于 Hermes + OpenCode 二次开发" → "AI Native Agent 架构"
  - feature card description："融合 Hermes Agent 的成熟架构" → "深度融合 AI Agent 与研发工具链"
- 修复时间：2026-07-01

## GAP-026：style.css .nav-nous-logo 类名
- 状态：✅ 已修复
- 修复文件：landingpage/style.css（第166行）
- 改动摘要：.nav-nous-logo → .nav-logo
- 修复时间：2026-07-01

## GAP-027：start.sh 硬编码 macos-arm64
- 状态：✅ 已修复
- 修复文件：embedded/start.sh
- 改动摘要：添加 uname -m 架构检测逻辑。arm64→macos-arm64/opencode，x86_64→macos-x64/opencode，不匹配时报错退出。添加 binary 存在性检查
- 修复时间：2026-07-01

## GAP-029：electron-output/ 混合旧版本文件
- 状态：✅ 已修复
- 修复文件：webui/dist/electron-output/（清理）
- 改动摘要：删除 Deep.Agent-0.6.22* DMG/ZIP/blockmap 文件和 builder-debug.yml，保留 v0.9.0-alpha.1 产物
- 修复时间：2026-07-01
