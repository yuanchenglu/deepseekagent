"""
测试 tool_schema_stabilizer (Tool Schema稳定器)
"""
import pytest
from deepagent_harness.tool_schema_stabilizer import (
    stabilize_tool_schemas, get_tools_fingerprint
)


class TestToolSchemaStabilizer:
    """Tool Schema稳定器测试"""

    def test_stabilize_sorts_tools_by_name(self):
        """测试工具按名称排序"""
        tools = [
            {"type": "function", "function": {"name": "z_tool", "description": "Z"}},
            {"type": "function", "function": {"name": "a_tool", "description": "A"}},
            {"type": "function", "function": {"name": "m_tool", "description": "M"}},
        ]
        result = stabilize_tool_schemas(tools)
        names = [t["function"]["name"] for t in result]
        assert names == ["a_tool", "m_tool", "z_tool"]

    def test_stabilize_none_returns_none(self):
        """测试None输入返回None"""
        assert stabilize_tool_schemas(None) is None
        assert stabilize_tool_schemas([]) == []

    def test_stabilize_does_not_modify_original(self):
        """测试不修改原始列表"""
        tools = [
            {"type": "function", "function": {"name": "b_tool"}},
            {"type": "function", "function": {"name": "a_tool"}},
        ]
        original_names = [t["function"]["name"] for t in tools]
        _ = stabilize_tool_schemas(tools)
        assert [t["function"]["name"] for t in tools] == original_names

    def test_fingerprint_consistent(self):
        """测试相同schema产生相同指纹"""
        tools = [
            {"type": "function", "function": {"name": "test", "description": "desc"}},
        ]
        fp1 = get_tools_fingerprint(tools)
        fp2 = get_tools_fingerprint(tools)
        assert fp1 == fp2
        assert len(fp1) == 16

    def test_fingerprint_different_for_different_tools(self):
        """测试不同schema产生不同指纹"""
        tools1 = [{"type": "function", "function": {"name": "a"}}]
        tools2 = [{"type": "function", "function": {"name": "b"}}]
        fp1 = get_tools_fingerprint(tools1)
        fp2 = get_tools_fingerprint(tools2)
        assert fp1 != fp2

    def test_fingerprint_no_tools(self):
        """测试无工具时的指纹"""
        fp = get_tools_fingerprint(None)
        assert fp == "no-tools"
        fp2 = get_tools_fingerprint([])
        assert fp2 == "no-tools"

    def test_description_none_becomes_empty_string(self):
        """测试 None description 不会被序列化为 'None' 字面量"""
        tools = [{
            "type": "function",
            "function": {
                "name": "test",
                "description": None,
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }]
        result = stabilize_tool_schemas(tools)
        assert result[0]["function"]["description"] == ""

    def test_description_non_string_cast(self):
        """测试非字符串 description 仍被 str() 转换"""
        tools = [{
            "type": "function",
            "function": {
                "name": "test",
                "description": 42,
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }]
        result = stabilize_tool_schemas(tools)
        assert result[0]["function"]["description"] == "42"

    def test_required_params_sorted(self):
        """测试required参数列表排序"""
        tools = [{
            "type": "function",
            "function": {
                "name": "test",
                "description": "test",
                "parameters": {
                    "type": "object",
                    "required": ["z", "a", "m"],
                    "properties": {}
                }
            }
        }]
        result = stabilize_tool_schemas(tools)
        required = result[0]["function"]["parameters"]["required"]
        assert required == ["a", "m", "z"]
