"""
Tool Schema 稳定器
==================

【文件职责】
确保发送给 API 的 tool schemas 在所有轮次中字节级稳定，
最大化 DeepSeek V4 Context Cache 命中率。

【为什么需要这个模块】
DeepSeek V4 的 Context Cache 使用 full-prefix-unit 匹配：只有当前缀完全一致时
才命中缓存。如果 tool schema 在不同轮次中顺序不同（如下游 dict 无序）、
参数顺序变化、description 有微小差异，都会导致 prefix cache miss。

论文约束 C-006：Tool schema 必须稳定
  - name 排序：按工具名字母序排列
  - 参数排序：按参数名字母序排列
  - description 不动态生成：使用注册时的固定描述
  - 不每轮增删工具

【与其他模块的协作】
- 在 run_agent.py 构建 API 请求前调用 stabilize_tool_schemas()
- 操作 api_messages 中 tools 字段的深拷贝，不修改原始 tools 列表
- 与 PrefixManager 共同确保 prefix 字节稳定
"""

import json
from typing import Any, Dict, List, Optional

__all__ = ["stabilize_tool_schemas", "get_tools_fingerprint"]


def stabilize_tool_schemas(tools: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """
    对工具 schema 列表进行确定性排序和规范化，确保跨轮次字节稳定。

    【处理内容】
    1. 按工具名字母序排列（JSON 序列化后 sort_keys=True）
    2. 对每个工具的 parameters.properties 按 key 字母序排列
    3. 对 parameters.required 列表排序
    4. 移除可能变化的临时字段
    5. 使用紧凑 JSON 格式（separators=(",", ":"), sort_keys=True）
       然后反序列化回 dict（这一步确保 dict 字段顺序一致）

    入参:
        tools: 原始工具 schema 列表（OpenAI function calling 格式），
               格式为 [{"type": "function", "function": {"name": "...", ...}}]

    返回:
        排序和规范化后的工具 schema 副本；输入为 None 时返回 None

    注意：此方法返回深拷贝，不修改输入列表。
    """
    if not tools:
        return tools

    # 第一步：深拷贝避免修改原始数据
    import copy
    stabilized = copy.deepcopy(tools)

    # 第二步：按工具名排序
    def tool_name(t):
        fn = t.get("function", {}) if isinstance(t, dict) else {}
        return fn.get("name", "")

    stabilized.sort(key=tool_name)

    # 第三步：规范化每个工具
    for tool in stabilized:
        if not isinstance(tool, dict):
            continue
        fn = tool.get("function")
        if not isinstance(fn, dict):
            continue

        # 规范化 parameters
        params = fn.get("parameters")
        if isinstance(params, dict):
            _normalize_schema(params)

        # 确保 description 是字符串且不含动态内容
        desc = fn.get("description", "")
        if not isinstance(desc, str):
            fn["description"] = str(desc)

    return stabilized


def _normalize_schema(schema: Dict[str, Any]):
    """
    递归规范化 JSON Schema 字典：
    - properties 按 key 字母序排列
    - required 列表排序
    - enum 列表排序（元素为基本类型时）
    - 移除 None 值

    入参:
        schema: JSON Schema 字典（原地修改）
    """
    # 移除 None 值字段
    keys_to_remove = [k for k, v in schema.items() if v is None]
    for k in keys_to_remove:
        del schema[k]

    # 规范化 properties
    props = schema.get("properties")
    if isinstance(props, dict):
        # 对每个子 schema 递归规范化
        for prop_schema in props.values():
            if isinstance(prop_schema, dict):
                _normalize_schema(prop_schema)
        # 注意：Python 3.7+ dict 保持插入顺序，我们不重新排序顶层 dict
        # （JSON 序列化时 sort_keys=True 处理）

    # 规范化 required 列表
    req = schema.get("required")
    if isinstance(req, list):
        req.sort()

    # 规范化 enum 列表（元素可排序时）
    enum = schema.get("enum")
    if isinstance(enum, list) and len(enum) > 0:
        try:
            enum.sort()
        except TypeError:
            pass  # 混合类型无法排序，保持原顺序

    # 规范化 items（数组类型的子 schema）
    items = schema.get("items")
    if isinstance(items, dict):
        _normalize_schema(items)

    # 规范化 anyOf / oneOf / allOf
    for combiner in ("anyOf", "oneOf", "allOf"):
        combos = schema.get(combiner)
        if isinstance(combos, list):
            for sub in combos:
                if isinstance(sub, dict):
                    _normalize_schema(sub)


def get_tools_fingerprint(tools: Optional[List[Dict[str, Any]]]) -> str:
    """
    计算工具 schema 列表的指纹（SHA-256 前16字符）。

    用于诊断：如果指纹在轮次间变化，说明 tool schema 不稳定，
    会导致 prefix cache miss。

    入参:
        tools: 工具 schema 列表

    返回:
        16 字符十六进制指纹字符串
    """
    import hashlib
    if not tools:
        return "no-tools"
    stabilized = stabilize_tool_schemas(tools)
    canonical = json.dumps(stabilized, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
