---
name: next-ai-draw-io
description: "AI 驱动的 draw.io 图表生成工具。自然语言 → 架构图/流程图/思维导图，支持实时预览、手绘草图识别、版本控制。通过 MCP 协议集成，工具名前缀 mcp_drawio_*。"
version: 1.0.0
author: 课程设计师
license: CC BY-NC-SA 4.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [drawio, diagrams, architecture, visualization, MCP]
    related_skills: [native-mcp]
    source: https://github.com/DayuanJiang/next-ai-draw-io
    stars: 31k+
---

# Next AI Draw.io — AI 图表生成 Skill

## 核心能力
- **自然语言生成图表**：一句话生成架构图、流程图、思维导图、ER图
- **手绘草图识别**：上传草图 → AI 自动生成正式图表
- **实时预览**：浏览器中实时看到图表生成过程
- **版本控制**：每次修改都有历史记录，可回滚
- **云架构专用支持**：AWS/GCP/Azure 架构图有专门优化
- **动画连接器**：支持动态/动画箭头连线

## MCP 工具列表（前缀 `mcp_drawio_`）

| 工具 | 用途 |
|------|------|
| `mcp_drawio_start_session` | 启动浏览器预览，返回 session URL |
| `mcp_drawio_create_new_diagram` | 从 XML 创建全新图表（会替换当前图表） |
| `mcp_drawio_edit_diagram` | 增量编辑：添加/更新/删除元素 |
| `mcp_drawio_get_diagram` | 获取当前图表 XML（编辑前必调用） |
| `mcp_drawio_export_diagram` | 导出为 .drawio / .png / .svg |
| `mcp_drawio_list_prompts` | 列出可用的提示词模板 |
| `mcp_drawio_get_prompt` | 获取指定提示词模板内容 |

## 工作流程

### 1. 创建新图表
```python
# Step 1: 启动会话
mcp_drawio_start_session()

# Step 2: 用 XML 创建图表
mcp_drawio_create_new_diagram(xml="<mxGraphModel>...</mxGraphModel>")

# Step 3: 导出
mcp_drawio_export_diagram(path="/tmp/output.png")
```

### 2. 编辑已有图表
```python
# Step 1: 获取当前状态（必须！）
mcp_drawio_get_diagram()

# Step 2: 用 cell_id 做增量编辑
mcp_drawio_edit_diagram(operations=[
    {"operation": "add", "cell_id": "new-1", "new_xml": "<mxCell ...>"},
    {"operation": "update", "cell_id": "existing-1", "new_xml": "<mxCell ...>"},
    {"operation": "delete", "cell_id": "old-1"}
])
```

## XML 格式参考

### 基本结构
```xml
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- 你的元素从 id="2" 开始 -->
  </root>
</mxGraphModel>
```

### 常用形状
```xml
<!-- 圆角矩形 -->
<mxCell id="2" value="服务器" style="rounded=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry"/>
</mxCell>

<!-- 圆形 -->
<mxCell id="3" value="数据库" style="ellipse;fillColor=#d5e8d4;strokeColor=#82b366;" vertex="1" parent="1">
  <mxGeometry x="300" y="100" width="100" height="80" as="geometry"/>
</mxCell>

<!-- 箭头连线 -->
<mxCell id="4" style="endArrow=classic;strokeColor=#666666;" edge="1" source="2" target="3" parent="1"/>
```

### 常用颜色方案
| 场景 | fill | stroke |
|------|------|--------|
| 用户/外部 | #fff2cc | #d6b656 |
| 服务/处理 | #dae8fc | #6c8ebf |
| 数据存储 | #d5e8d4 | #82b366 |
| 异常/警告 | #f8cecc | #b85450 |
| 中间件 | #e1d5e7 | #9673a6 |

## 常见图表模板

### 系统架构图
```
prompt: 生成一个微服务架构图，包含 API Gateway、用户服务、订单服务、数据库，用箭头表示调用关系
```

### 流程图
```
prompt: 画一个用户登录流程：输入账号密码 → 验证 → 通过则跳转首页，失败则提示错误
```

### 思维导图
```
prompt: 创建 AI 学习路线思维导图，包含基础数学、Python、机器学习、深度学习、NLP 五个分支
```

### ER 图
```
prompt: 画一个电商系统 ER 图，包含用户、订单、商品、分类四个表，标注主外键关系
```

## 注意事项
- `create_new_diagram` 会**替换整个图表**，仅用于全新创建
- `edit_diagram` 保留用户手动修改（会先获取浏览器最新状态）
- 编辑已有图表前**必须先调用 `get_diagram`** 获取 cell_id
- XML 中所有 id 必须唯一
- 导出 PNG 时图表会自动适配画布大小
