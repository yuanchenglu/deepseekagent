"""Tests for Cognitive Loop Guidance in prompt_builder."""

from agent.prompt_builder import build_cognitive_loop_guidance, COGNITIVE_LOOP_GUIDANCE


def test_build_cognitive_loop_guidance_returns_string():
    """返回的引导段是字符串。"""
    section = build_cognitive_loop_guidance()
    assert isinstance(section, str)
    assert len(section) > 0


def test_cognitive_loop_guidance_contains_key_concepts():
    """引导段包含三层认知核心理念。"""
    section = build_cognitive_loop_guidance()
    assert "荣辱观" in section
    assert "思维方式" in section
    assert "三省吾身" in section
    assert "先内后外" in section
