"""Tests for environments/tool_call_parsers — decorator-based handler registry."""

import importlib
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# Mock openai before importing parsers (CI may not have openai installed)
_openai_mod = MagicMock(__name__="openai", __package__="openai")
_openai_types = MagicMock(__name__="openai.types", __package__="openai.types")
_openai_chat = MagicMock(
    __name__="openai.types.chat", __package__="openai.types.chat"
)
_openai_tool_call = MagicMock(
    __name__="openai.types.chat.chat_completion_message_tool_call",
    __package__="openai.types.chat.chat_completion_message_tool_call",
)
_openai_tool_call.ChatCompletionMessageToolCall = SimpleNamespace
_openai_tool_call.Function = SimpleNamespace

sys.modules["openai"] = _openai_mod
sys.modules["openai.types"] = _openai_types
sys.modules["openai.types.chat"] = _openai_chat
sys.modules["openai.types.chat.chat_completion_message_tool_call"] = _openai_tool_call

from environments.tool_call_parsers import (
    PARSER_REGISTRY,
    ToolCallParser,
    get_parser,
    list_parsers,
    register_parser,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_registry():
    """Save and restore PARSER_REGISTRY around each test."""
    saved = dict(PARSER_REGISTRY)
    PARSER_REGISTRY.clear()
    yield
    PARSER_REGISTRY.clear()
    PARSER_REGISTRY.update(saved)


# ---------------------------------------------------------------------------
# @register_parser decorator
# ---------------------------------------------------------------------------


class TestRegisterParser:
    def test_registers_class(self):
        @register_parser("test_a")
        class TestParser(ToolCallParser):
            def parse(self, text):
                return text, None

        assert "test_a" in PARSER_REGISTRY
        assert PARSER_REGISTRY["test_a"] is TestParser

    def test_overwrites_existing_name(self):
        @register_parser("dup")
        class ParserA(ToolCallParser):
            def parse(self, text):
                return text, None

        @register_parser("dup")
        class ParserB(ToolCallParser):
            def parse(self, text):
                return text, None

        assert PARSER_REGISTRY["dup"] is ParserB

    def test_preserves_class_identity(self):
        """Decorator returns the same class, not a wrapper."""
        @register_parser("identity")
        class MyParser(ToolCallParser):
            def parse(self, text):
                return text, None

        assert PARSER_REGISTRY["identity"] is MyParser

    def test_rejects_empty_name(self):
        with pytest.raises(ValueError, match="non-empty string"):
            @register_parser("")
            class Empty(ToolCallParser):
                def parse(self, text):
                    return text, None

    def test_rejects_whitespace_name(self):
        with pytest.raises(ValueError, match="non-empty string"):
            @register_parser("   ")
            class Whitespace(ToolCallParser):
                def parse(self, text):
                    return text, None

    def test_rejects_non_string_name(self):
        with pytest.raises(ValueError, match="non-empty string"):
            @register_parser(123)  # type: ignore
            class BadType(ToolCallParser):
                def parse(self, text):
                    return text, None


# ---------------------------------------------------------------------------
# get_parser()
# ---------------------------------------------------------------------------


class TestGetParser:
    def test_returns_instance_for_registered_parser(self):
        @register_parser("magic")
        class MagicParser(ToolCallParser):
            def parse(self, text):
                return "parsed", None

        parser = get_parser("magic")
        assert isinstance(parser, MagicParser)

    def test_returns_new_instance_each_call(self):
        @register_parser("multi")
        class MultiParser(ToolCallParser):
            def parse(self, text):
                return text, None

        p1 = get_parser("multi")
        p2 = get_parser("multi")
        assert p1 is not p2

    def test_raises_key_error_for_unknown_name(self):
        with pytest.raises(KeyError, match="not found"):
            get_parser("nonexistent")

    def test_error_lists_available_parsers(self):
        @register_parser("alpha")
        class Alpha(ToolCallParser):
            def parse(self, text):
                return text, None

        @register_parser("beta")
        class Beta(ToolCallParser):
            def parse(self, text):
                return text, None

        with pytest.raises(KeyError) as exc:
            get_parser("unknown")
        assert "alpha" in str(exc.value)
        assert "beta" in str(exc.value)


# ---------------------------------------------------------------------------
# list_parsers()
# ---------------------------------------------------------------------------


class TestListParsers:
    def test_returns_empty_when_no_parsers(self):
        assert list_parsers() == []

    def test_returns_sorted_names(self):
        @register_parser("z")
        class Z(ToolCallParser):
            def parse(self, text):
                return text, None

        @register_parser("a")
        class A(ToolCallParser):
            def parse(self, text):
                return text, None

        @register_parser("m")
        class M(ToolCallParser):
            def parse(self, text):
                return text, None

        assert list_parsers() == ["a", "m", "z"]


# ---------------------------------------------------------------------------
# ToolCallParser base class
# ---------------------------------------------------------------------------


class TestToolCallParserBase:
    def test_cannot_instantiate_abstract(self):
        """ABC prevents direct instantiation without implementing parse()."""
        with pytest.raises(TypeError):
            ToolCallParser()

    def test_concrete_subclass_instantiates(self):
        class GoodParser(ToolCallParser):
            def parse(self, text):
                return text, None

        instance = GoodParser()
        assert isinstance(instance, ToolCallParser)

    def test_parse_returns_tuple(self):
        class SimpleParser(ToolCallParser):
            def parse(self, text):
                return "content", []

        content, calls = SimpleParser().parse("hello")
        assert content == "content"
        assert calls == []

    def test_parse_can_return_none_content(self):
        class NoContentParser(ToolCallParser):
            def parse(self, text):
                return None, None

        content, calls = NoContentParser().parse("<tool_call>{}</tool_call>")
        assert content is None
        assert calls is None


# ---------------------------------------------------------------------------
# Full registry — import-time registration
# ---------------------------------------------------------------------------


class TestFullRegistry:
    """Integration tests: after importing all parser modules."""

    _PARSER_SUBMODULES = [
        "environments.tool_call_parsers.hermes_parser",
        "environments.tool_call_parsers.longcat_parser",
        "environments.tool_call_parsers.mistral_parser",
        "environments.tool_call_parsers.llama_parser",
        "environments.tool_call_parsers.qwen_parser",
        "environments.tool_call_parsers.deepseek_v3_parser",
        "environments.tool_call_parsers.deepseek_v3_1_parser",
        "environments.tool_call_parsers.kimi_k2_parser",
        "environments.tool_call_parsers.glm45_parser",
        "environments.tool_call_parsers.glm47_parser",
        "environments.tool_call_parsers.qwen3_coder_parser",
    ]

    def _reload_parsers(self):
        """Force a full re-import of the parser package to trigger @register_parser."""
        mod = importlib.import_module("environments.tool_call_parsers")
        # Remove submodule cache so __init__'s imports re-execute
        for sub in self._PARSER_SUBMODULES:
            sys.modules.pop(sub, None)
        importlib.reload(mod)

    def test_all_parsers_imported_and_registered(self):
        """Trigger all @register_parser decorators by reloading the module."""
        self._reload_parsers()

        names = list_parsers()
        assert "hermes" in names
        assert "mistral" in names
        assert "llama3_json" in names
        assert "deepseek_v3" in names
        assert "deepseek_v3_1" in names
        assert "kimi_k2" in names
        assert "glm45" in names
        assert "glm47" in names
        assert "qwen3_coder" in names

    def test_each_parser_is_instantiable(self):
        self._reload_parsers()

        for name in list_parsers():
            parser = get_parser(name)
            # Check interface conformance (isinstance fails after reload
            # since base class objects differ across reload)
            assert hasattr(parser, "parse")
            result = parser.parse("hello")
            assert isinstance(result, tuple)
            assert len(result) == 2
