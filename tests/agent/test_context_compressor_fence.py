"""Tests for context_compressor Cognitive Index fence protection."""

import pytest
from agent.context_compressor import ContextCompressor


def test_fence_content_is_preserved_during_compression():
    """验证 compress() 方法过滤带有 cognitive fence 的消息。"""
    compressor = ContextCompressor(
        model="test-model",
        threshold_percent=0.01,
        protect_first_n=1,
        protect_last_n=1,
        quiet_mode=True,
        config_context_length=128000,
    )

    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {
            "role": "assistant",
            "content": "-----COGNITIVE_INDEX_START-----\nmemory content\n-----COGNITIVE_INDEX_END-----",
        },
        {"role": "user", "content": "more conversation"},
        {"role": "assistant", "content": "more response"},
    ]

    # 强制压缩
    compressor.threshold_tokens = 1
    compressed = compressor.compress(messages)

    # 验证围栏内容未丢失（不在压缩范围内时仍被保留）
    compressed_text = ""
    for msg in compressed:
        if isinstance(msg.get("content"), str):
            compressed_text += msg["content"]

    assert "memory content" in compressed_text, "Cognitive index content should be preserved"
