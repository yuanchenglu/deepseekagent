# Project-Level oh-my-openagent 配置手法

## 原理

OMO 的 `findProjectOpencodePluginConfigFiles()` 函数从 `process.cwd()` 向上遍历目录树，
在每个目录的 `.opencode/` 下搜索 `oh-my-openagent.json`（或旧名 `oh-my-opencode.json`）。
所有找到的 config 按最近→最远优先级**合并**。

## 配置链

```
1. <project>/.opencode/oh-my-openagent.json     ← 项目级（最近，最高优先级）
2. <parent>/.opencode/oh-my-openagent.json      ← 父目录级（向上遍历）
3. ~/.config/opencode/oh-my-openagent.json      ← 全局
4. ~/.config/opencode/oh-my-opencode.json       ← 旧名（自动迁移）
```

## 典型配置：最强推理

```jsonc
// <project>/.opencode/oh-my-openagent.json
{
  "agents": {
    "sisyphus": {
      "model": "opencodego/deepseek-v4-flash",
      "reasoningEffort": "max"
    },
    "prometheus": {
      "model": "opencodego/deepseek-v4-pro",
      "reasoningEffort": "max"
    }
    // ... 其他 agent 同理
  },
  "categories": {
    "deep": {
      "model": "opencodego/deepseek-v4-pro",
      "reasoningEffort": "max"
    }
    // ... 其他 category 同理
  }
}
```

支持的 `reasoningEffort`：`max`、`xhigh`、`high`、`medium`、`low`、`minimal`、`none`。

## 配合 OpenSpec 初始化

```bash
cd <project>
openspec init --tools opencode
# 生成 .opencode/commands/ 和 .opencode/skills/
```

## 加入 .gitignore

```gitignore
# Project-level oh-my-openagent config (user-specific)
.opencode/oh-my-openagent.json
```
