"""
DeepAgent Harness 场景路由测试
"""
import pytest
from deepagent_harness import SceneRouter, SceneType


@pytest.fixture
def router():
    return SceneRouter()


class TestSceneClassification:
    """场景分类准确率测试"""

    def test_code_scene(self, router):
        """研发类指令"""
        assert router.classify("实现用户登录功能") == SceneType.CODE
        assert router.classify("修复bug") == SceneType.CODE
        assert router.classify("写一个RESTful API") == SceneType.CODE
        assert router.classify("重构用户模块代码") == SceneType.CODE

    def test_research_scene(self, router):
        """研究类指令"""
        assert router.classify("调研一下最新的AI框架") == SceneType.RESEARCH
        assert router.classify("对比React和Vue的优缺点") == SceneType.RESEARCH
        assert router.classify("分析两种技术方案的差异") == SceneType.RESEARCH

    def test_query_scene(self, router):
        """问答类指令"""
        assert router.classify("什么是微服务架构？") == SceneType.QUERY
        assert router.classify("Docker怎么用") == SceneType.QUERY
        assert router.classify("解释一下Kubernetes") == SceneType.QUERY

    def test_planning_scene(self, router):
        """规划类指令"""
        assert router.classify("帮我写一个技术方案") == SceneType.PLANNING
        assert router.classify("设计系统架构") == SceneType.PLANNING
        assert router.classify("规划下个季度的研发路线图") == SceneType.PLANNING

    def test_operation_scene(self, router):
        """运维类指令"""
        assert router.classify("部署到生产环境") == SceneType.OPERATION
        assert router.classify("配置nginx反向代理") == SceneType.OPERATION

    def test_other_scene(self, router):
        """其他类"""
        assert router.classify("今天天气怎么样") == SceneType.OTHER
        assert router.classify("你叫什么名字") == SceneType.OTHER

    def test_route_code_auto_dispatch(self, router):
        """研发类指令自动路由到 Code Mode"""
        result = router.route("实现一个文件上传功能")
        assert result["status"] == "completed"
        assert result.get("via_harness") is True
        assert result.get("scene_type") == "code"

    def test_route_non_code_passthrough(self, router):
        """非研发类指令返回 passthrough"""
        result = router.route("今天天气怎么样")
        assert result["status"] == "passthrough"
        assert result.get("scene_type") == "other"

    def test_is_code_detection(self, router):
        assert router.is_code(SceneType.CODE) is True
        assert router.is_code(SceneType.OTHER) is False
        assert router.is_code(SceneType.QUERY) is False

    def test_route_instruction_shortcut(self):
        """快捷函数"""
        from deepagent_harness import route_instruction
        result = route_instruction("修复登录bug")
        assert result["status"] == "completed"


class TestEdgeCases:
    """边界情况测试：中英文混合、特殊字符、空字符串"""

    def test_mixed_chinese_english_instruction(self):
        """中英文混合指令"""
        from deepagent_harness import SceneRouter
        router = SceneRouter()

        # 中英文混合
        result = router.classify("帮我 implement a login API 加 JWT 认证")
        # 应被识别为研发类（包含"实现/API/认证"等关键词）
        assert result is not None

        result2 = router.classify("fix the bug 在订单模块中")
        assert result2 is not None

        result3 = router.classify("调研一下 the latest AI frameworks in 2024")
        assert result3 is not None

    def test_special_characters_instruction(self):
        """特殊字符指令"""
        from deepagent_harness import SceneRouter, SceneType
        router = SceneRouter()

        # 各种特殊字符
        special_cases = [
            "!!!紧急修复生产环境bug@@@",
            "实现功能【用户管理】#重要#",
            "修复>>登录失败<<的bug",
            "配置nginx——反向代理（生产环境）",
            "***调研***最新***技术***",
            "写一个 API：/users/{id}",
            "实现 ＡＢＣ（全角字母）功能",
            "测试·点·分隔符",
        ]

        for case in special_cases:
            result = router.classify(case)
            assert result is not None, f"特殊字符指令 '{case}' 返回 None"
            # 不应崩溃，SceneType 枚举值应有效
            assert isinstance(result, SceneType), f"特殊字符指令 '{case}' 返回类型错误"

    def test_empty_string(self):
        """空字符串"""
        from deepagent_harness import SceneRouter
        router = SceneRouter()

        result = router.classify("")
        assert result is not None, "空字符串应返回 SceneType.OTHER"
        # 空字符串应归类为 OTHER
        from deepagent_harness import SceneType
        assert result == SceneType.OTHER, f"空字符串应归类为 OTHER，实际为 {result}"

    def test_whitespace_only(self):
        """纯空白字符"""
        from deepagent_harness import SceneRouter, SceneType
        router = SceneRouter()

        result = router.classify("   ")
        assert result == SceneType.OTHER, f"纯空白应归类为 OTHER，实际为 {result}"

        result2 = router.classify("\t\n\r")
        assert result2 == SceneType.OTHER, f"空白字符应归类为 OTHER"

    def test_html_or_markdown_mixed(self):
        """HTML/Markdown 混合指令"""
        from deepagent_harness import SceneRouter
        router = SceneRouter()

        cases = [
            "实现一个表单：<input type='text' name='username'>",
            "修复 **加粗** 文字中的 bug",
            "写一个 API：`GET /users`",
            "用 ```python``` 写一个函数",
        ]

        for case in cases:
            result = router.classify(case)
            assert result is not None, f"混合指令 '{case[:30]}' 不应返回 None"
            # 不应崩溃
            result2 = router.route(case)
            assert isinstance(result2, dict)
            assert "status" in result2
