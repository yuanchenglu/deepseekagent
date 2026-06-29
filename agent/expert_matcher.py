"""专家匹配器（StarRoad Cognition）。
对接 The Agency 的 232 专家库（~/.config/opencode/agents/）。
根据 route_name + 关键词匹配最佳专家。"""

# === DeepAgent: StarRoad Cognition ===

from __future__ import annotations
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Agency 16 个 division 到 route_name 的映射，用于缩小匹配范围
ROUTE_TO_DIVISIONS = {
    "implement": ["Engineering", "Game Dev", "Spatial Computing"],
    "analyze": ["Security", "Testing", "Finance"],
    "research": ["Product", "Marketing", "Specialized", "GIS"],
    "discuss": ["Product", "Marketing", "Design", "Sales", "Project Mgmt"],
    "simple": [],  # 简单任务不需要匹配专家
}

# 默认 Agency 安装路径（由 Agency 工具管理，非 Hermes/DeepAgent 路径）
DEFAULT_AGENTS_DIR = Path.home() / ".config" / "opencode" / "agents"


@dataclass
class Expert:
    """专家对象。"""
    slug: str         # 如 "software-architect"
    name: str         # 如 "Software Architect"
    division: str     # 如 "Engineering"
    prompt: str       # 完整的 system prompt（从 .md 文件读取）


class ExpertMatcher:
    """对接 The Agency 的 232 专家库。

    用法：
        matcher = ExpertMatcher()
        experts = matcher.match("帮我设计数据库表", "implement")
        # 返回 [Expert("backend-architect"), Expert("database-optimizer")]
    """

    def __init__(self, agents_dir: str | Path | None = None):
        """初始化 ExpertMatcher。

        Args:
            agents_dir: Agency 专家 .md 文件目录，默认 ~/.config/opencode/agents/
        """
        if agents_dir is None:
            agents_dir = DEFAULT_AGENTS_DIR
        self._agents_dir = Path(agents_dir)
        # 缓存：slug -> {"slug", "name", "division", "description"}
        self._registry: dict[str, dict] = {}
        # prompt 缓存：slug -> str（避免重复文件 IO）
        self._prompt_cache: dict[str, str] = {}

    def match(self, message: str, route_name: str, top_n: int = 2) -> list[Expert]:
        """根据 route_name + 关键词查找最匹配的专家。

        Args:
            message: 用户消息
            route_name: 'discuss' | 'implement' | 'analyze' | 'research' | 'simple'
            top_n: 返回 top N 个专家

        Returns:
            list[Expert] — 按匹配度排序。route_name='simple' 时返回空列表。
        """
        if route_name == "simple":
            return []

        # 确保缓存已加载
        if not self._registry:
            self.refresh_cache()

        # 根据 route_name 过滤可用的 division
        target_divisions = ROUTE_TO_DIVISIONS.get(route_name, [])
        candidates = list(self._registry.values())
        if target_divisions:
            candidates = [c for c in candidates if c.get("division") in target_divisions]

        if not candidates:
            # 降级：返回所有可用专家
            candidates = list(self._registry.values())

        # 关键词匹配评分
        keywords = self._extract_keywords(message)
        scored = []
        for candidate in candidates:
            score = self._score_match(candidate, keywords, route_name)
            if score > 0:
                scored.append((score, candidate))

        # 按分数排序，取 top_n
        scored.sort(key=lambda x: x[0], reverse=True)
        top_candidates = [c for _, c in scored[:top_n]]

        # 如果没有匹配，使用默认专家
        if not top_candidates:
            default_slugs = {
                "implement": "software-architect",
                "analyze": "code-reviewer",
                "research": "trend-researcher",
                "discuss": "product-manager",
            }
            slug = default_slugs.get(route_name, "software-architect")
            # 在 Engineering division 中查找默认专家
            experts = self.get_experts_for_division("Engineering")
            for exp in experts:
                if exp.slug == slug:
                    top_candidates = [{"slug": slug, "name": exp.name, "division": exp.division}]
                    break

        # 加载 expert prompt
        result = []
        for c in top_candidates:
            prompt = self.load_expert_prompt(c["slug"])
            result.append(Expert(
                slug=c["slug"],
                name=c["name"],
                division=c.get("division", ""),
                prompt=prompt,
            ))

        return result

    def load_expert_prompt(self, slug: str) -> str:
        """读取对应 .md 文件，提取 content 作为 system prompt。

        缓存已读取的 prompt，避免重复文件 IO。
        """
        if slug in self._prompt_cache:
            return self._prompt_cache[slug]

        path = self._agents_dir / f"{slug}.md"
        if not path.exists():
            logger.warning("ExpertMatcher: agent file not found: %s", path)
            self._prompt_cache[slug] = ""
            return ""

        try:
            content = path.read_text(encoding="utf-8").strip()
            self._prompt_cache[slug] = content
            return content
        except Exception as e:
            logger.warning("ExpertMatcher: failed to read %s: %s", path, e)
            self._prompt_cache[slug] = ""
            return ""

    def get_available_experts(self) -> list[dict]:
        """返回所有可用专家的摘要列表（slug + name + division + description）。"""
        if not self._registry:
            self.refresh_cache()
        return [
            {"slug": v["slug"], "name": v["name"], "division": v.get("division", ""),
             "description": v.get("description", "")}
            for v in self._registry.values()
        ]

    def get_experts_for_division(self, division: str) -> list[Expert]:
        """按 division 获取专家列表。"""
        if not self._registry:
            self.refresh_cache()
        experts = []
        for v in self._registry.values():
            if v.get("division") == division:
                prompt = self.load_expert_prompt(v["slug"])
                experts.append(Expert(
                    slug=v["slug"],
                    name=v["name"],
                    division=division,
                    prompt=prompt,
                ))
        return experts

    def refresh_cache(self) -> None:
        """重建专家注册表缓存。

        扫描 agents_dir 下所有 .md 文件，提取 frontmatter 中的元数据。
        """
        self._registry = {}
        if not self._agents_dir.exists():
            logger.warning("ExpertMatcher: agents dir not found: %s", self._agents_dir)
            return

        for md_file in sorted(self._agents_dir.glob("*.md")):
            try:
                metadata = self._parse_agent_file(md_file)
                if metadata:
                    self._registry[metadata["slug"]] = metadata
            except Exception as e:
                logger.debug("ExpertMatcher: failed to parse %s: %s", md_file.name, e)

        logger.info("ExpertMatcher: loaded %d experts from %s", len(self._registry), self._agents_dir)

    # -- 内部方法 --

    def _parse_agent_file(self, path: Path) -> dict | None:
        """解析单个 agent .md 文件，提取 frontmatter 元数据。

        Agency 的 .md 文件格式：
            ---
            name: Software Architect
            division: Engineering
            description: ...
            ---
            (system prompt content)
        """
        slug = path.stem
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None

        # 解析 frontmatter
        name = slug.replace("-", " ").title()
        division = "Engineering"
        description = ""

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if fm_match:
            fm_text = fm_match.group(1)
            for line in fm_text.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip().lower()
                    value = value.strip().strip("\"'")
                    if key == "name":
                        name = value
                    elif key == "division":
                        division = value
                    elif key == "description":
                        description = value

        return {
            "slug": slug,
            "name": name,
            "division": division,
            "description": description,
        }

    @staticmethod
    def _extract_keywords(message: str) -> list[str]:
        """从消息中提取关键领域词。"""
        # 领域关键词（扩展自 Agency 决策矩阵）
        domain_keywords = {
            "前端": ["前端", "react", "vue", "angular", "ui", "界面", "component"],
            "后端": ["后端", "api", "数据库", "server", "服务端", "接口"],
            "安全": ["安全", "security", "漏洞", "渗透", "加密", "auth"],
            "架构": ["架构", "设计模式", "系统设计", "模块", "微服务"],
            "测试": ["测试", "test", "unit", "e2e", "集成", "mock"],
            "数据": ["数据", "etl", "管道", "pipeline", "分析", "报表"],
            "部署": ["部署", "devops", "ci/cd", "docker", "k8s", "发布"],
            "设计": ["设计", "ui", "ux", "品牌", "视觉", "交互"],
            "策略": ["策略", "战略", "方向", "规划", "路线", "roadmap"],
            "调研": ["调研", "研究", "竞品", "趋势", "对比", "分析"],
        }

        msg_lower = message.lower()
        found = []
        for domain, keywords in domain_keywords.items():
            for kw in keywords:
                if kw in msg_lower:
                    found.append(kw)
                    break
        return found

    @staticmethod
    def _score_match(candidate: dict, keywords: list[str], route_name: str) -> int:
        """计算候选专家的匹配分数。"""
        score = 0
        candidate_text = f"{candidate.get('name', '')} {candidate.get('description', '')}".lower()

        # 关键词匹配
        for kw in keywords:
            if kw in candidate_text:
                score += 10

        # division 匹配加分
        division = candidate.get("division", "").lower()
        if route_name == "implement" and division in ("engineering", "game dev"):
            score += 5
        elif route_name == "analyze" and division in ("security", "testing"):
            score += 5
        elif route_name == "research" and division in ("product", "marketing"):
            score += 5

        return score
