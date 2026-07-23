"""
Deep Agent Harness — 场景路由（Scene Router）

核心功能：
1. 将用户指令按场景分类：研发 / 研究 / 问答 / 规划 / 其他
2. 研发类指令自动路由到 Code Mode 内置研发小组
3. 其他场景由 Agent 直接处理

这是 "Modern + Harness + Scene = Agent" 中 Scene 层的核心实现。

使用方法：
    from deepagent_harness.scene_router import SceneRouter, SceneType
    
    router = SceneRouter()
    scene = router.classify("帮我实现用户登录功能")
    # SceneType.CODE
    
    if router.is_code(scene):
        router.route_to_code_mode("用户登录功能")
"""

from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path


class SceneType(Enum):
    """场景类型分类"""
    CODE = "code"             # 研发类：实现功能、写代码、修bug
    RESEARCH = "research"     # 研究类：调研技术、对比方案
    QUERY = "query"           # 问答类：查询信息、解释概念
    PLANNING = "planning"     # 规划类：出方案、写文档、设计架构
    OPERATION = "operation"   # 运维类：部署、配置、监控
    OTHER = "other"           # 其他


# 关键词→场景映射（MVP 阶段用关键词，后续可升级为小模型分类）
_SCENE_KEYWORDS: Dict[SceneType, list] = {
    SceneType.CODE: [
        "实现", "开发", "写代码", "编码", "编程", "修复", "bug",
        "实现功能", "添加功能", "重构", "refactor", "feature",
        "创建文件", "创建模块", "创建函数", "创建类",
        "前端", "后端", "API", "接口", "数据库",
        "登录", "注册", "权限", "认证", "鉴权",
        "修改", "改动", "变更",
    ],
    SceneType.RESEARCH: [
        "调研", "研究", "对比", "比较", "分析",
        "技术选型", "方案对比", "benchmark", "性能",
        "优缺点", "优劣", "区别", "差异",
    ],
    SceneType.PLANNING: [
        # 注意：不要用"架构"这种宽泛词，会把"什么是微服务架构？"误判为 PLANNING。
        # 用更长/更具体的组合词来指代"做架构设计"这个动作。
        "方案", "写方案", "出方案", "设计方案", "设计文档",
        "架构设计", "系统架构", "架构规划", "技术架构",
        "规划", "计划", "做计划",
        "文档", "PRD", "技术方案",
        "路线图", "roadmap", "里程碑",
    ],
    SceneType.OPERATION: [
        "部署", "发布", "上线", "配置", "运维",
        "安装", "启动", "停止", "重启",
        "监控", "日志", "排查", "诊断",
    ],
    SceneType.QUERY: [
        "什么是", "什么意思", "怎么用", "如何",
        "解释", "介绍", "说明", "是什么",
    ],
}


class SceneRouter:
    """
    场景路由器 — 分析用户指令，确定场景类型并路由。
    MVP 使用关键词分类，后续可升级为小模型。
    """

    def __init__(self):
        self._keyword_map = _SCENE_KEYWORDS
        # 迭代顺序即优先级——先匹配到哪个就返回哪个。
        # 修复历史问题：docstring 声明 "CODE > RESEARCH > PLANNING > OPERATION > QUERY"
        # 但旧实现把 QUERY 放在第一位，导致 "如何实现 X" 被误判为 QUERY。
        # 现与 docstring 对齐：CODE 最优先（核心业务——研发任务要进 Code Mode）。
        self._scene_order = [
            SceneType.CODE,
            SceneType.RESEARCH,
            SceneType.PLANNING,
            SceneType.OPERATION,
            SceneType.QUERY,
        ]

    def classify(self, instruction: str) -> SceneType:
        """
        分析用户指令，返回匹配的场景类型。
        
        优先级：CODE > RESEARCH > PLANNING > OPERATION > QUERY > OTHER
        """
        instruction_lower = instruction.lower()

        for scene_type in self._scene_order:
            keywords = self._keyword_map.get(scene_type, [])
            for kw in keywords:
                if kw.lower() in instruction_lower or kw in instruction:
                    return scene_type

        return SceneType.OTHER

    def is_code(self, scene_type: SceneType) -> bool:
        """判断是否为研发场景"""
        return scene_type == SceneType.CODE

    def route_to_code_mode(self, instruction: str) -> Dict[str, Any]:
        """将研发类指令路由到 Code Mode 内置研发小组"""
        try:
            from deepagent_code_mode import handle_development_request
            result = handle_development_request(instruction)
            result["scene"] = "code"
            result["via_harness"] = True
            return result
        except ImportError:
            return {
                "status": "error",
                "scene": "code",
                "message": "Code Mode 模块未加载，请先安装 deepagent_code_mode",
            }

    def route(self, instruction: str) -> Dict[str, Any]:
        """
        全自动路由：分类 + 执行一步走。
        研发类→Code Mode，其他→由 Agent 自行处理（返回路由建议）。
        """
        scene = self.classify(instruction)

        if self.is_code(scene):
            result = self.route_to_code_mode(instruction)
            result["scene_type"] = scene.value
            return result

        # 非研发类：返回路由建议，让 Agent 直接处理
        return {
            "status": "passthrough",
            "scene_type": scene.value,
            "message": f"场景类型: {scene.value}，由 Agent 直接处理",
        }


# 快捷函数
def route_instruction(instruction: str) -> Dict[str, Any]:
    """快捷路由入口"""
    router = SceneRouter()
    return router.route(instruction)


def route_enhanced(instruction: str) -> Dict[str, Any]:
    """
    增强路由：三路由层（语义路由→专家匹配→执行路由）

    Layer 1: 语义路由（SceneRouter 关键词分类）
    Layer 2: 专家匹配（IntentRouter 意图分类+策略绑定）
    Layer 3: 执行路由（CODE→Code Mode，其他→direct）
    """
    # Layer 1: 语义路由
    router = SceneRouter()
    scene_type = router.classify(instruction)

    # Layer 2: 专家匹配（意图路由）
    from deepagent_harness.intent_router import IntentRouter
    intent_router = IntentRouter()
    intent, strategy = intent_router.classify_and_get_strategy(
        instruction, scene_type.value
    )
    route_context = intent_router.get_route_context(intent, strategy)

    # Layer 3: 执行路由
    execution = router.route(instruction)

    return {
        "scene_type": scene_type.value,
        "intent": intent.value,
        "strategy": {
            "interview_depth": strategy.interview_depth,
            "plan_granularity": strategy.plan_granularity,
            "review_standard": strategy.review_standard,
            "execution_mode": strategy.execution_mode,
            "model_tier_hint": strategy.model_tier_hint,
        },
        "route_context": route_context,
        "execution": execution,
        "starroad_l1": True,
        "starroad_l2": True,
        "starroad_l3": True,
    }
