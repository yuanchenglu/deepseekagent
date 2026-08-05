# DESK-007 受控 Preview 用户测试任务包

## Work ID: DESK-007
## 执行人/AI: local-ai
## 复核人/Owner: 小路
## 仓库: yuanchenglu/deepseekagent

本文件是受控 Preview 用户测试的预定义任务包。由 1-2 名受控用户在干净 Apple Silicon Mac 上执行，local-ai 汇总证据。

---

## 一、环境要求

- 干净 Apple Silicon Mac（macOS 最新稳定版）
- 已安装：Hermes Agent + OpenCode（验证共存）
- 网络：能访问 deepseekagent.starseas.org
- 前置：`bash -c "$(curl -fsSL https://deepseekagent.starseas.org/install.sh)" -- --channel beta`

## 二、预定义任务（用户执行，逐项记录）

### T1. 安装与首次启动
1. 从官网安装 DeepAgent Core（beta channel），记录退出码
2. 下载 unsigned Preview DMG（deepseekagent.starseas.org/releases/desktop/）
3. 挂载 DMG，拖 DeepAgent.app 到 Applications
4. **双击尝试** → 预期弹"已损坏"或"无法验证开发者"
5. **右键 → 打开 → 仍要打开** → 预期正常启动
6. 记录：弹窗文案、绕过步骤是否与下载页指引一致

### T2. DeepAgent 模式真实任务
1. Preview 启动后进入 DeepAgent（assistant）模式
2. 完成真实任务：让助手创建一个文本文件并写入指定内容
3. 记录：任务成功率、响应时间、模型

### T3. DeepCode 模式真实任务
1. 切换到 DeepCode（code）模式
2. 完成真实编码任务：让助手写一个 Python 函数并运行
3. 记录：任务成功率、响应时间、模型

### T4. 模式切换
1. DeepAgent ↔ DeepCode 往返切换 3 次
2. 记录：切换是否流畅、有无报错、进程/端口变化

### T5. 升级路径
1. 触发"检查更新"（菜单或自动）
2. 记录：是否检测到最新版、下载进度、安装提示
3. 不执行安装（Preview 未 publish 时预期无可用更新）

### T6. 共存验证
1. Preview 运行时同时启动 Hermes CLI 和 OpenCode
2. 三者各自完成一个简单任务
3. 记录：端口、PID、目录互不干扰

### T7. 卸载
1. 删除 DeepAgent.app（拖到废纸篓）
2. 运行 `deepagent uninstall`
3. 记录：残留文件、用户数据是否保留

## 三、反馈模板（用户逐项填写）

| 任务 | 结果(通过/失败/部分) | 退出码 | 关键日志 | 问题描述 | 缺陷编号 |
|------|---------------------|--------|---------|---------|---------|
| T1 | | | | | |
| T2 | | | | | |
| T3 | | | | | |
| T4 | | | | | |
| T5 | | | | | |
| T6 | | | | | |
| T7 | | | | | |

补充问题：
1. 首次启动困惑点（弹窗文案 vs 下载页指引是否一致）
2. 卡顿/崩溃/无响应（附时间点）
3. 其他反馈

## 四、证据汇总（local-ai 执行）

- 收集用户反馈表 → 统计任务成功率
- 问题分级：P0（阻断）/P1（严重）/P2（体验）
- 汇总为 DESK-007 evidence 文件

## 五、Go/No-Go 标准

- 所有 T1-T7 主路径通过（允许 P2 体验问题）
- 任务成功率 >= 90%
- 无 P0/P1 未关闭

## 六、依赖

- 本任务包依赖 DESK-006 的 DeepAgent Core 安装（网络恢复或 CI 验证）
- 需要真实受控用户执行

## 七、下一 Work ID: DESK-008

DESK-008：根据 DESK-007 反馈清零 P0/P1。
