"""
硬约束提取器
============

【文件职责】
从用户自然语言输入中确定性地提取"硬约束"——即用户使用"禁止/不能/必须/务必"等
强指令词表达的不可违反的要求。提取后的约束被注入到 System Prompt 的冻结前缀区，
实现与对话历史的物理隔离（不参与上下文压缩），确保模型在长对话中始终遵守。

【为什么不用 LLM 提取】
论文 I-04 明确指出：硬约束提取必须是确定性的，不能依赖 LLM 判断。原因：
1. LLM 可能漏判/误判（注意力稀释后更严重）
2. 每次提取消耗额外 token
3. 提取结果不稳定（同一输入可能提取出不同约束）
正则匹配零成本、确定性、结果稳定。

【设计原则】
- 零 LLM 调用：纯正则表达式，速度快、成本零
- 误匹配过滤：排除"我不需要帮助"等非约束性用法
- 分类标记：每条约束标记为"禁止类"（prohibition）或"必须类"（requirement）
- 去重：相同内容不重复提取

【与其他模块的协作】
- 在 run_agent.py 的 pre-turn 阶段被调用（处理首条用户消息）
- 提取结果传给 PrefixManager.freeze() 时拼接到冻结前缀
- 提取结果传给 ImmuneSystem.post_execution_review() 作为审查依据
- format_for_prefix() 的输出直接嵌入 System Prompt

参考文献：I-04 KV Cache 硬约束前缀注入
"""

import re
from dataclasses import dataclass, field
from typing import List

__all__ = ["HardConstraint", "HardConstraintExtractor",
           "extract_hard_constraints", "format_constraints_for_prefix"]


@dataclass
class HardConstraint:
    """
    单条硬约束的数据结构。

    属性说明:
        text:            原始约束文本（完整的一句话，包含触发词）
        source:          约束来源标识，如 "user_prompt"/"config"/"skill"/"system"
        constraint_type: "prohibition"（禁止类：不要/不能/禁止做的事）
                         或 "requirement"（必须类：必须/务必要做的事）
        keywords:        从约束中提取的关键词列表（供免疫系统做违反检测）
    """
    text: str
    source: str
    constraint_type: str  # "prohibition" 或 "requirement"
    keywords: List[str] = field(default_factory=list)


# ── 正则模式定义 ──────────────────────────────────────────────
# 禁止类触发词：不要/不可以/不能/禁止/严禁/不准/不得/千万别/绝不要
# 后面跟 2-80 个字符（不含句末标点）作为约束内容
_PROHIBITION_PATTERNS = [
    re.compile(r"(?:不要|不可以|不能|禁止|严禁|不准|不得|千万别|绝不要|绝对不要)\s*([^。！？\n]{2,80})"),
    # "别/勿" 开头的短语（更短：1-79 字符，因为"别X"通常更简洁）
    re.compile(r"(?:别|勿)\s*([^\s，。！？\n][^。！？\n]{1,79})"),
]

# 必须类触发词：必须/一定要/务必/需要/确保/请一定/千万要/应当/应该
_REQUIREMENT_PATTERNS = [
    re.compile(r"(?:必须|一定要|务必|需要|确保|请一定|千万要|应当|应该)\s*([^。！？\n]{2,80})"),
]

# 误匹配过滤模式：这些情况虽然触发了关键词但不是约束
_FALSE_POSITIVE_PATTERNS = [
    # "我不需要帮助"等表述个人状态的用法，不是对 Agent 的约束
    re.compile(r"我不需要|我不要|别管我|不要问我|不用你|我不想"),
    # "你能不能？""要不要？"等疑问句，不是指令
    re.compile(r"^(?:你)?(?:能不?能|要不要|可不可以|是不是)[?？]?"),
    # 引用/代码块中的"不要"（如文档中举例）
    re.compile(r"['\"`].*?(?:不要|不能|禁止).*?['\"`]"),
]


class HardConstraintExtractor:
    """
    硬约束提取器

    【类职责】
    从用户输入文本中使用正则表达式确定性地提取硬约束。
    不调用 LLM，纯字符串处理，毫秒级完成。

    【典型用法】
        extractor = HardConstraintExtractor()
        constraints = extractor.extract("必须使用中文，禁止删除数据库")
        # → [HardConstraint(text="必须使用中文", type="requirement"),
        #    HardConstraint(text="禁止删除数据库", type="prohibition")]
        prefix_text = extractor.format_for_prefix(constraints)
        # → 格式化后的 Markdown 文本，直接嵌入 System Prompt
    """

    def extract(self, text: str, source: str = "user_prompt") -> List[HardConstraint]:
        """
        从文本中提取所有硬约束。

        入参:
            text:   用户输入文本（通常是 session 第一条消息）
            source: 来源标识，默认为 "user_prompt"

        返回:
            HardConstraint 列表，按在文本中出现的顺序排列

        处理流程:
            1. 遍历所有禁止类模式，匹配后检查是否为误匹配
            2. 遍历所有必须类模式，同上
            3. 去重（相同归一化文本只保留一条）
            4. 为每条约束提取关键词
        """
        constraints: List[HardConstraint] = []
        seen_texts = set()  # 用于去重：归一化（去空白）后的文本集合

        # ── 提取禁止类约束 ──
        for pattern in _PROHIBITION_PATTERNS:
            for match in pattern.finditer(text):
                full_match = match.group(0).strip()
                if self._is_false_positive(full_match):
                    continue
                # 归一化：去除所有空白字符用于去重比较
                normalized = re.sub(r"\s+", "", full_match)
                if normalized in seen_texts:
                    continue
                seen_texts.add(normalized)
                keywords = self._extract_keywords(match.group(1))
                constraints.append(HardConstraint(
                    text=full_match,
                    source=source,
                    constraint_type="prohibition",
                    keywords=keywords,
                ))

        # ── 提取必须类约束 ──
        for pattern in _REQUIREMENT_PATTERNS:
            for match in pattern.finditer(text):
                full_match = match.group(0).strip()
                if self._is_false_positive(full_match):
                    continue
                normalized = re.sub(r"\s+", "", full_match)
                if normalized in seen_texts:
                    continue
                seen_texts.add(normalized)
                keywords = self._extract_keywords(match.group(1))
                constraints.append(HardConstraint(
                    text=full_match,
                    source=source,
                    constraint_type="requirement",
                    keywords=keywords,
                ))

        return constraints

    def format_for_prefix(self, constraints: List[HardConstraint]) -> str:
        """
        将硬约束列表格式化为嵌入 System Prompt 冻结前缀区的 Markdown 文本。

        入参:
            constraints: extract() 返回的约束列表

        返回:
            格式化后的 Markdown 文本。无约束时返回空字符串。

        输出格式示例:
            ## 硬性约束（必须严格遵守，不可违反）

            以下是用户明确提出的硬性要求...

            ### 禁止事项:
            1. ❌ 禁止删除数据库
            ### 必须做到:
            1. ✅ 必须使用中文回复

        设计决策：为什么用 ❌/✅ emoji？
            视觉上快速区分禁止/必须，降低模型在长上下文中遗漏的概率。
            emoji 在 tokenization 中通常是单个 token，成本极低。
        """
        if not constraints:
            return ""

        lines = [
            "## 硬性约束（必须严格遵守，不可违反）",
            "",
            "以下是用户明确提出的硬性要求，你在整个对话过程中必须始终遵守：",
        ]

        # 按类型分组：先列禁止类，再列必须类
        prohibitions = [c for c in constraints if c.constraint_type == "prohibition"]
        requirements = [c for c in constraints if c.constraint_type == "requirement"]

        if prohibitions:
            lines.append("")
            lines.append("### 禁止事项：")
            for i, c in enumerate(prohibitions, 1):
                lines.append(f"{i}. ❌ {c.text}")

        if requirements:
            lines.append("")
            lines.append("### 必须做到：")
            for i, c in enumerate(requirements, 1):
                lines.append(f"{i}. ✅ {c.text}")

        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _is_false_positive(self, text: str) -> bool:
        """
        判断匹配到的文本是否为误匹配（不是真正的约束）。

        入参:
            text: 正则匹配到的完整文本（含触发词）

        返回:
            True 表示是误匹配（应该跳过），False 表示是真正的约束

        误匹配场景:
            - "我不需要你的帮助" → 是表达个人意愿，不是对 Agent 行为的约束
            - "你能不能帮我？" → 疑问句，不是指令
            - 代码块/引用中的"不要" → 是举例而非约束
        """
        for fp_pattern in _FALSE_POSITIVE_PATTERNS:
            if fp_pattern.search(text):
                return True
        return False

    def _extract_keywords(self, action_text: str) -> List[str]:
        """
        从约束动作文本中提取关键词，供免疫系统做违反检测。

        入参:
            action_text: 约束中触发词后面的动作描述部分

        返回:
            最多 10 个关键词（中英文混合，长度≥2的词）

        简单策略：按非字符分割，取长度≥2的词。
        不使用 jieba 等分词库，避免额外依赖。
        免疫系统只需要粗略的关键词匹配来检测明显的违反。
        """
        words = re.findall(r"[\u4e00-\u9fa5a-zA-Z]{2,}", action_text)
        return words[:10]  # 最多取 10 个关键词，避免噪声


# ── 模块级单例（便捷函数）────────────────────────────────────
# 提供模块级便捷函数，避免每次都创建实例
_extractor = HardConstraintExtractor()


def extract_hard_constraints(text: str, source: str = "user_prompt") -> List[HardConstraint]:
    """便捷函数：从文本提取硬约束（使用全局单例）。"""
    return _extractor.extract(text, source)


def format_constraints_for_prefix(constraints: List[HardConstraint]) -> str:
    """便捷函数：格式化约束为前缀文本（使用全局单例）。"""
    return _extractor.format_for_prefix(constraints)
