# 技术深度对比分析方法论

> 用于评价多个开源项目对**特定技术/模型架构的优化深度**，区别于通用的"二开选型"评估。
> 核心问题不是"有没有支持X模型"，而是**"针对X模型的架构特性做了哪些底层优化"**。

---

## 适用场景

- 评估多个推理引擎对 DeepSeek/VLLM/其他模型的优化深度
- 对比多个框架对同一技术的实现方式（如 MLA Attention 的 CUDA vs Triton 实现）
- 技术选型决策：需要理解各项目的实际工程水平，而不仅看 Stars

## 关键原则：Integration vs Optimization

这是最重要的区分：

| 层次 | 特征 | 例子 |
|------|------|------|
| **API Integration** | 通过 OpenAI 兼容接口调用模型，无专用 kernel | AgentOS 的 DeepSeek provider |
| **Model Support** | 能加载模型权重、推理，但用通用算子 | 早期的 HuggingFace transformers |
| **Architecture Optimization** | 针对模型独有架构写自定义 kernel | vLLM 的 FlashMLA、SGLang 的 Triton MLA |
| **Hardware Co-Design** | 联合硬件特性做算子级优化 | TensorRT-LLM 的 FP8 算子融合 |

**调研时必须在报告中明确标注每个项目处于哪个层次。**

---

## 研究流程

### Step 1: 界定优化维度

分析目标模型的架构特征，确定需要关注的优化维度。

示例（DeepSeek）：
```
架构特征 → 优化维度
├── MLA (Multi-head Latent Attention) → Attention kernel, KV cache 压缩
├── MoE (Mixture of Experts) → 专家并行、负载均衡
├── FP8 训练 → FP8 量化推理
├── 长上下文 (128K-1M) → 分页缓存、前缀缓存
└── 671B 总参数 → 模型并行、多节点部署
```

### Step 2: 项目筛选

**多策略搜索（适应受限网络）：**

```bash
# 策略1: 搜索 API + 关键词（可能被限流）
curl -s "https://api.github.com/search/repositories?q=deepseek+optimization&sort=stars&o=desc"

# 策略2: 单项目 API（更稳定，不限流）
curl -s "https://api.github.com/repos/{owner}/{repo}"

# 策略3: 精筛内容搜索
curl -s "https://api.github.com/search/code?q=deepseek+repo:{owner}/{repo}+path:csrc"
# 注：code search 需 token，且 public repo 有限额
```

**China 网络下的备选方案：**
- 优先用单项目 API 逐一查知名项目（比 search API 稳定）
- 结合预训练知识补充网络无法触及的内容
- 在报告中标注哪些信息来自"code inspection" vs "known facts"

### Step 3: 逐项目深度分析

对每个项目，回答以下问题：

```
1. 基础元数据：Stars, Language, License, 最近更新
2. 支持程度：是 API 集成还是架构优化？
3. 优化清单：
   ├── 是否有自定义 CUDA/Triton kernel？
   ├── 是否有针对模型架构的专用代码路径？
   └── 是否有专用配置文件/示例？
4. 关键文件路径：README, model definition, kernel code
5. 部署场景：生产集群 / 单卡 GPU / 边缘设备 / CPU
```

### Step 4: 构建对比矩阵

**按技术层组织矩阵**（这是与通用评估最大的区别）：

| 项目 | Layer1: Attention | Layer2: Quantization | Layer3: MoE | Layer4: Deployment |
|------|------------------|---------------------|-------------|-------------------|
| **vLLM** | 手写 CUDA FlashMLA | FP8 动态 KV Cache | 专家并行+负载均衡 | 生产集群 |
| **SGLang** | Triton MLA | FP8 | ✅ | 生产 |

**每个维度内用粒度描述：** ⭐ 数量表示深度，具体技术名称为补充。

### Step 5: 生成决策树

```
用户需求
├── ⭐ 生产高吞吐 → vLLM（最成熟）
├── ⭐ 长上下文 → SGLang（RadixAttention）
├── ⭐ 本地边缘 → llama.cpp（GGUF）
└── ⭐ 微调 → unsloth（显存节省80%）
```

### Step 6: 编写结论

**报告结构（按顺序）：**

1. **前置知识** — 目标模型架构的独特特征（让读者理解"为什么需要专门优化"）
2. **项目总览表** — 10-15个候选，含 Stars/Language/License
3. **逐项目详细分析** — 每个 200-300 字，含优化清单和关键文件
4. **对比矩阵** — 按技术层组织的多维对比
5. **决策树** — 按场景推荐
6. **结论** — 一句话推荐 + 关键认知

---

## 常见陷阱

### ❌ 只看 README 不看代码
- README 说 "supports DeepSeek" 不一定有专有优化
- 必须找：自定义 kernel 文件、模型定义中的专用代码路径

### ❌ 只凭 Stars 判断优化深度
- TensorRT-LLM (13k stars) 的 DeepSeek 优化深度可能超过某些 30k star 项目
- 硬件绑定（NVIDIA only）会限制 stars 但可能技术更深

### ❌ 把"集成"当"优化"
- AgentOS 有 DeepSeek provider 文件 → 这是集成不是优化
- vLLM 有 FlashMLA CUDA kernel → 这是优化

### ❌ 忽略项目关系
- AutoGPTQ 生成的量化模型 → 被 vLLM/llama.cpp 加载
- HuggingFace transformers → 被 unsloth/lmdeploy 作为基座
- 理解上下游关系才能正确评价

---

## 输出格式

**推荐：Markdown 报告**（非 HTML）
- 技术对比更适合结构化的 Markdown（表格、代码块、列表）
- 报告保存到 `~/Documents/ObsidianVault/000-Tmp/` 对应目录
- 文件命名：`[技术]-[模型]-对比报告.md`

---

*本文件是 open-source-project-evaluator 的变体方法论，侧重技术深度而非二开选型。*
