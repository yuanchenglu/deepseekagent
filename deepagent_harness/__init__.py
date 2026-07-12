"""DeepAgent Harness 包 — DeepSeek V4 深度适配层

包含模块：
- scene_router: 场景路由（已有，新增 route_enhanced 增强路由）
- prefix_manager: Byte-Stable Prefix 架构（冻结前缀+变更注入尾部）
- hard_constraint: KV Cache 硬约束前缀注入（确定性关键词提取）
- model_router: Flash/Pro 智能路由（Flash-first, Pro-on-checkpoint）
- reasoning_manager: Reasoning Content 管理（Provider感知的消息过滤）
- intent_router: 7+1 意图路由（细粒度任务分类+策略绑定）
- immune_system: Agent 免疫系统（执行后约束审查+Skill固化）
- starroad_cognition: StarRoad 三层认知引擎（L1荣辱观/L2方法论/L3反省）
- context_layout: Context Layout 管理器（sliding_window=128 近端锚点）
- tool_schema_stabilizer: Tool Schema 稳定器（字节级确定性排序）
"""
from .scene_router import SceneRouter, SceneType, route_instruction, route_enhanced
from .prefix_manager import PrefixManager
from .hard_constraint import HardConstraint, HardConstraintExtractor, extract_hard_constraints, format_constraints_for_prefix
from .model_router import ModelRouter, ModelTier, RouteDecision
from .reasoning_manager import ReasoningManager
from .intent_router import IntentRouter, IntentType, IntentStrategy
from .immune_system import ImmuneSystem, Violation, ImmuneResult
from .starroad_cognition import StarRoadCognition, MEMORY_TIERS
from .context_layout import ContextLayoutManager
from .tool_schema_stabilizer import stabilize_tool_schemas, get_tools_fingerprint

__all__ = [
    # 场景路由
    "SceneRouter", "SceneType", "route_instruction", "route_enhanced",
    # Byte-Stable Prefix
    "PrefixManager",
    # 硬约束注入
    "HardConstraint", "HardConstraintExtractor",
    "extract_hard_constraints", "format_constraints_for_prefix",
    # Flash/Pro 路由
    "ModelRouter", "ModelTier", "RouteDecision",
    # Reasoning 管理
    "ReasoningManager",
    # 意图路由
    "IntentRouter", "IntentType", "IntentStrategy",
    # 免疫系统
    "ImmuneSystem", "Violation", "ImmuneResult",
    # StarRoad 认知
    "StarRoadCognition", "MEMORY_TIERS",
    # 上下文布局
    "ContextLayoutManager",
    # Tool Schema 稳定器
    "stabilize_tool_schemas", "get_tools_fingerprint",
]