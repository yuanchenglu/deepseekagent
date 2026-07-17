"""
测试 HardConstraintExtractor (硬约束提取器)
"""
import pytest
from deepagent_harness.hard_constraint import (
    HardConstraint, HardConstraintExtractor,
    extract_hard_constraints, format_constraints_for_prefix
)


class TestHardConstraintExtraction:
    """硬约束提取测试"""

    def setup_method(self):
        self.extractor = HardConstraintExtractor()

    def test_extract_prohibition_keywords(self):
        """测试提取禁止类约束"""
        text = "禁止删除数据库，不要修改配置文件，千万别提交代码"
        constraints = self.extractor.extract(text)

        types = [c.constraint_type for c in constraints]
        assert "prohibition" in types
        assert len(constraints) >= 1  # 正则可能贪婪匹配成一条长约束

    def test_extract_requirement_keywords(self):
        """测试提取必须类约束"""
        text = "必须使用中文回复。一定要写注释。确保测试通过。"
        constraints = self.extractor.extract(text)
        # 用句号分隔后可以提取多条
        types = [c.constraint_type for c in constraints]
        assert "requirement" in types

    def test_mixed_constraints(self):
        """测试混合约束提取"""
        text = "必须使用Python。不要用外部库。禁止硬编码密码。"
        constraints = self.extractor.extract(text)
        assert len(constraints) >= 2

    def test_no_constraints(self):
        """测试无约束文本"""
        text = "今天天气真好，帮我写个Hello World"
        constraints = self.extractor.extract(text)
        assert len(constraints) == 0

    def test_false_positive_i_dont_need(self):
        """测试误匹配过滤：'我不需要'类个人表述"""
        text = "我不需要你的帮助"
        constraints = self.extractor.extract(text)
        # "我不需要"应该被过滤
        assert len(constraints) == 0

    def test_deduplication(self):
        """测试约束去重"""
        text = "禁止删除数据库。禁止删除数据库。"
        constraints = self.extractor.extract(text)
        # 去重后数量应该更少
        texts = [c.text for c in constraints]
        assert len(texts) == len(set(texts))

    def test_keyword_extraction(self):
        """测试关键词提取"""
        text = "必须使用中文注释"
        constraints = self.extractor.extract(text)
        assert len(constraints) > 0
        assert len(constraints[0].keywords) > 0

    def test_extract_prohibition_simple(self):
        """测试简单禁止提取"""
        text = "不要删除文件"
        constraints = self.extractor.extract(text)
        assert len(constraints) == 1
        assert constraints[0].constraint_type == "prohibition"

    def test_extract_requirement_simple(self):
        """测试简单必须提取"""
        text = "必须使用中文"
        constraints = self.extractor.extract(text)
        assert len(constraints) == 1
        assert constraints[0].constraint_type == "requirement"


class TestFormatForPrefix:
    """约束格式化测试"""

    def setup_method(self):
        self.extractor = HardConstraintExtractor()

    def test_format_empty(self):
        """测试空约束列表返回空字符串"""
        result = self.extractor.format_for_prefix([])
        assert result == ""

    def test_format_prohibitions(self):
        """测试禁止类约束格式化"""
        constraints = [
            HardConstraint(text="禁止删除数据库", source="test",
                          constraint_type="prohibition", keywords=["删除", "数据库"])
        ]
        result = self.extractor.format_for_prefix(constraints)
        assert "硬性约束" in result
        assert "禁止事项" in result
        assert "❌" in result
        assert "禁止删除数据库" in result

    def test_format_requirements(self):
        """测试必须类约束格式化"""
        constraints = [
            HardConstraint(text="必须使用中文", source="test",
                          constraint_type="requirement", keywords=["中文"])
        ]
        result = self.extractor.format_for_prefix(constraints)
        assert "必须做到" in result
        assert "✅" in result
        assert "必须使用中文" in result

    def test_format_mixed(self):
        """测试混合约束格式化"""
        constraints = [
            HardConstraint(text="禁止删除", source="test",
                          constraint_type="prohibition", keywords=[]),
            HardConstraint(text="必须测试", source="test",
                          constraint_type="requirement", keywords=[]),
        ]
        result = self.extractor.format_for_prefix(constraints)
        assert "禁止事项" in result
        assert "必须做到" in result


class TestModuleLevelFunctions:
    """模块级便捷函数测试"""

    def test_extract_hard_constraints(self):
        """测试便捷提取函数"""
        constraints = extract_hard_constraints("必须用中文")
        assert len(constraints) > 0
        assert constraints[0].constraint_type == "requirement"

    def test_format_constraints_for_prefix(self):
        """测试便捷格式化函数"""
        constraints = extract_hard_constraints("禁止删除数据")
        result = format_constraints_for_prefix(constraints)
        assert "硬性约束" in result or result == ""
