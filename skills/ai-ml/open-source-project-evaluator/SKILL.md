---
name: open-source-project-evaluator
description: |
  Systematic evaluation and comparison of open-source projects from GitHub for secondary development.
  Conducts multi-keyword searches, analyzes projects against specific criteria (stars, activity, tech stack, 
  mobile support, localization, customization difficulty), and produces a comprehensive HTML comparison report.
  
  Trigger phrases: "找一下开源", "GitHub上搜索", "开源方案调研", "对比一下开源项目", 
  "评估开源项目", "有没有开源的", "推荐开源方案", "开源项目对比", "二开选型"
tags:
  - research
  - github
  - open-source
  - comparison
  - evaluation
  - html-report
---

# 开源项目选型评估器

当用户需要在GitHub上寻找开源项目作为二次开发基础时使用。系统性地搜索、评估、对比多个项目，最终输出一份包含可视化图表的HTML对比报告。

## 适用场景

- 寻找特定功能领域的开源解决方案
- 评估多个开源项目的二开可行性
- 为技术选型提供数据支撑
- 快速了解某领域的开源生态

## 评估流程

### 第一步：明确需求

与用户确认以下关键信息：

| 维度 | 问题 |
|-----|------|
| **功能需求** | 需要实现什么核心功能？ |
| **技术偏好** | 有偏好的技术栈吗？（Python/PHP/Java/Node等） |
| **团队规模** | 多少人使用？技术能力如何？ |
| **移动端** | 是否需要移动端支持？ |
| **本地化** | 是否需要中文支持？ |
| **预算/工期** | 二开预算和时间预期？ |

### 第二步：多关键词搜索

使用多个相关关键词并行搜索，确保覆盖面：

```
关键词组合策略：
1. [核心功能] + [system/software]
2. [核心功能] + [open source/github]
3. [应用场景] + [management/ERP]
4. [技术栈] + [核心功能]
```

**搜索技巧：**
- 使用GitHub搜索API或浏览器访问 `github.com/search`
- 按Stars排序（`s=stars&o=desc`）
- 过滤语言（`language:Python`, `language:PHP`）
- 查看最近更新时间（活跃度指标）

**处理GitHub限流：**
- 如果遇到"Too many requests"错误，等待几分钟后重试
- 或使用已掌握的知识结合有限的搜索结果
- 优先评估高Stars的知名项目

### 第三步：项目筛选与评估

从搜索结果中筛选Top 10-15个项目，按以下维度评估：

#### 基础指标

| 指标 | 权重 | 说明 |
|-----|-----|------|
| Stars | 20% | 社区认可度 |
| 最近更新 | 20% | 项目活跃度 |
| Forks | 10% | 开发者关注度 |
| Issues响应 | 10% | 维护质量 |

#### 功能匹配度

| 指标 | 权重 | 评估方法 |
|-----|-----|---------|
| 核心功能覆盖 | 15% | README功能列表对比 |
| 扩展性 | 15% | 插件/模块机制 |
| 文档完整度 | 10% | Wiki、文档站点 |

#### 二开友好度

| 指标 | 评估要点 |
|-----|---------|
| 代码结构 | 是否清晰、模块化 |
| 技术栈流行度 | 是否主流、易招人 |
| 数据库设计 | 是否合理、易扩展 |
| API设计 | RESTful、文档完善 |
| 测试覆盖 | 单元测试、CI/CD |

#### 特殊需求评估

- **移动端支持**：原生App、PWA、响应式Web？
- **中文支持**：官方中文、社区翻译、需汉化？
- **部署难度**：Docker、一键脚本、手动配置？

### 第四步：深度分析Top项目

对筛选出的Top 5-10个项目进行深度分析：

**每个项目分析模板：**

```markdown
## #[排名] [项目名]

**基础信息**
- GitHub: [链接]
- Stars: [数量]
- 技术栈: [标签]
- 许可证: [License]

**核心功能**
- [功能1]
- [功能2]
- ...

**优点**
1. [优点1]
2. [优点2]
3. ...

**缺点**
1. [缺点1]
2. [缺点2]
3. ...

**二开评估**
- 难度: [低/中/高]
- 学习曲线: [短/中/长]
- 社区支持: [活跃/一般/冷清]

**适用场景**
[描述最适合的使用场景]
```

### 第五步：生成HTML对比报告

创建一份视觉丰富、交互友好的HTML报告：

**报告结构：**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <!-- Tailwind CSS + Chart.js -->
</head>
<body>
    <!-- 1. Hero区域：标题+概述 -->
    
    <!-- 2. 需求概述：用户原始需求 -->
    
    <!-- 3. Top N项目卡片：
         - 每个项目独立卡片
         - 左侧：排名+Stars+技术栈
         - 右侧：优缺点对比+评分
    -->
    
    <!-- 4. 可视化对比：
         - 雷达图：多维度能力对比
         - 柱状图：综合评分排名
         - 表格：详细指标对比
    -->
    
    <!-- 5. 推荐方案：
         - 首选推荐（大卡片）
         - 备选方案（小卡片）
         - 实施路线图
    -->
    
    <!-- 6. 成本估算 -->
    
</body>
</html>
```

**视觉设计要点：**

1. **使用Tailwind CSS**：快速构建现代UI
2. **Chart.js图表**：雷达图、柱状图展示对比
3. **卡片式布局**：每个项目独立卡片，hover效果
4. **颜色编码**：
   - 优点：绿色系
   - 缺点：红色系
   - 技术栈标签：蓝色系
   - 评分：渐变色
5. **响应式设计**：适配手机和桌面

**HTML模板关键代码：**

```html
<!-- 项目卡片示例 -->
<div class="bg-white rounded-2xl shadow-lg overflow-hidden card-hover">
    <div class="flex flex-col lg:flex-row">
        <!-- 左侧：项目标识 -->
        <div class="lg:w-1/4 gradient-bg p-6 text-white">
            <div class="rank-badge">#1</div>
            <h3>ProjectName</h3>
            <div class="stars">⭐ 6,925</div>
            <div class="tech-tags">
                <span>Python</span>
                <span>Django</span>
            </div>
        </div>
        <!-- 右侧：详细分析 -->
        <div class="lg:w-3/4 p-6">
            <!-- 优缺点对比 -->
            <div class="grid md:grid-cols-2 gap-4">
                <div class="bg-green-50 p-4 rounded-lg">
                    <h4>优点</h4>
                    <ul>...</ul>
                </div>
                <div class="bg-red-50 p-4 rounded-lg">
                    <h4>缺点</h4>
                    <ul>...</ul>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Chart.js雷达图 -->
<canvas id="radarChart"></canvas>
<script>
new Chart(document.getElementById('radarChart'), {
    type: 'radar',
    data: {
        labels: ['功能完整度', '移动端', '二开友好度', '中文支持', '活跃度', '文档'],
        datasets: [...]
    }
});
</script>
```

### 第六步：推荐与实施建议

**推荐方案结构：**

1. **首选推荐**（大卡片突出显示）
   - 推荐理由（3-5条）
   - 定制开发建议
   - 预估工期

2. **备选方案**（2-3个小卡片）
   - 适用场景说明
   - 优缺点速览

3. **实施路线图**
   - 时间线可视化
   - 里程碑标记

4. **成本估算**
   - 开发成本
   - 交付周期
   - 运维成本

## 评估维度详解

### 二开难度评估标准

| 难度 | 特征 | 代表项目 |
|-----|------|---------|
| **低** | 单体应用、代码<1万行、文档齐全、有插件机制 | Dolibarr |
| **中** | MVC框架、代码1-5万行、API完善 | Laravel项目 |
| **高** | 微服务、代码>5万行、自定义框架 | Odoo、ERPNext |

### 移动端支持分级

| 级别 | 说明 | 评估 |
|-----|------|------|
| ✅ 原生支持 | 有iOS/Android App | 最佳 |
| ⚠️ PWA | 渐进式Web应用 | 良好 |
| ⚠️ 响应式 | 适配移动端的Web | 可用 |
| ❌ 不支持 | 仅桌面端 | 需额外开发 |

### 中文支持评估

| 级别 | 说明 |
|-----|------|
| ✅ 原生中文 | 官方提供中文界面 |
| ✅ 社区翻译 | 有完整的中文语言包 |
| ⚠️ 需汉化 | 需要自行翻译 |
| ❌ 无支持 | 仅英文 |

## 常见领域关键词参考

### 进销存/ERP领域
- inventory management system
- stock management
- warehouse management (WMS)
- ERP system
- point of sale (POS)
- accounting software

### 技术栈过滤
- `language:Python` - Python项目
- `language:PHP` - PHP项目
- `language:JavaScript` - Node.js项目
- `language:TypeScript` - TypeScript项目

### 排序与过滤
- `s=stars&o=desc` - 按Stars降序
- `pushed:>2024-01-01` - 最近有更新
- `archived:false` - 未归档

## 输出交付

**主要交付物：**
1. **HTML报告** - 可视化对比报告，可直接浏览器打开
2. **Markdown摘要** - 纯文本版本，便于分享

**报告命名规范：**
```
[领域]-开源项目调研报告-v[版本].html
例：进销存财务系统-开源项目调研报告-v1.0.html
```

## 质检清单

交付前自检：

- [ ] 是否覆盖了至少3个不同的搜索关键词？
- [ ] Top项目是否按Stars/活跃度综合排序？
- [ ] 每个项目是否都有优缺点分析？
- [ ] 是否包含技术栈标签？
- [ ] 移动端和中文支持是否明确标注？
- [ ] 是否包含可视化图表（雷达图/柱状图）？
- [ ] 是否有明确的推荐方案？
- [ ] 是否提供实施路线图？
- [ ] HTML是否在浏览器中正常显示？

## 变体：技术深度对比分析

对于评价多个项目对**特定技术/模型架构的优化深度**（不是二开选型），使用 `references/technical-deep-dive-comparison.md` 方法论。核心差异：

| 维度 | 通用评估（本 skill） | 技术深度对比（变体） |
|------|--------------------|--------------------|
| 评估目标 | 哪个项目更适合二开 | 哪个项目的优化技术更深 |
| 核心问题 | 功能全、易修改、社区活跃 | 有无自定义 kernel、架构适配 |
| 输出格式 | HTML 可视化报告 | Markdown 对比矩阵 + 决策树 |
| 关键区分 | 不强调 | 必须区分 "API 集成" vs "架构优化" |

当用户问"XX 项目对 YY 模型做了哪些优化"或"对比各项目对 XX 技术的支持深度"时，加载该参考文件。

### 变体 C：迁移/替换决策

对于**已有产品在生产环境运行，想评估是否切换到另一个已知产品**的场景，使用 `references/migration-decision-analysis.md` 方法论。核心差异：

| 维度 | 通用评估（本 skill） | 迁移决策（变体 C） |
|------|--------------------|--------------------|
| 评估目标 | 哪个项目最适合从零开始 | 迁移收益 > 迁移成本 + 风险？ |
| 候选人 | 多个未知项目 | 已知两个对比对象 |
| 核心问题 | 功能全、易修改、社区活跃 | 增量价值是否卡脖子？迁移成本是否可控？ |
| 输出格式 | HTML 可视化报告 | Markdown 对比矩阵 + 决策树 |
| 推荐类型 | 首选/备选 | 保留/迁移/并行部署 |

当用户问"我现在用着 X，要不要换成 Y？"或"对比 X 和 Y 哪个更适合我的现有部署"时，加载该参考文件。

### 变体 D：Issue 健康度分析

对于**需要评估一个开源项目的 Issue 真实修复状态**的场景（尤其是批量关闭后），使用 `references/issue-health-analysis.md` 方法论。核心差异：

| 维度 | 通用评估（本 skill） | Issue 健康度分析（变体 D） |
|------|--------------------|--------------------|
| 评估目标 | 哪个项目更适合二开 | 项目的 Bug 修复率和子系统健康度 |
| 候选人 | 多个未知项目 | 一个已知项目的全部 Issue |
| 核心方法 | 搜索 + 功能对比 | 分类 + Git commit 交叉验证 |
| 输出格式 | HTML 可视化报告 | Markdown 表格 + 修复率统计 |
| 关键区分 | 项目间横向对比 | 项目的纵向深度审计 |

当用户问"这项目的 Issue 是真的修了还是只是关了"或"帮我分析这个项目的 Issue 健康度"时，加载该参考文件。

---

## ⚠️ 关键注意事项（经验教训）

### 用户指定搜索范围时，必须严格遵守

**Pitfall（经验教训）：** 如果用户明确说"在GitHub上搜"，就只搜GitHub，不要自己扩展到其他来源（如百度、知乎、新闻网站等）。用户说"你搜一下他们的官网" → 用户要的是官网信息，但这是在特定场景下。

**正确做法：**
- 用户说"在GitHub上搜" → 只用GitHub API/搜索
- 用户说"搜一下官网" → 优先访问官网
- 用户说"不要搜其他无用信息" → 严格限制搜索范围
- 用户提供了特定信息源（如飞书文档链接）→ 优先尝试该来源

**错误做法（被用户纠正过）：**
- ❌ 用户说"GitHub上搜"，自己去web搜索
- ❌ 用户说"不要搜其他无用信息"，还是用了其他来源
- ❌ 用户提供了飞书文档链接，自己去其他地方搜

### 其他注意事项

1. **GitHub限流**：频繁搜索可能触发限流，需要等待或换方式
2. **项目活跃度**：优先选择近半年有更新的项目
3. **License检查**：注意开源协议是否允许商用/二开
4. **技术栈匹配**：考虑团队的技术能力选择合适的技术栈
5. **社区规模**：Stars少但活跃的项目可能比Stars多但停滞的项目更好

---

*Created for systematic open-source project evaluation and comparison*
