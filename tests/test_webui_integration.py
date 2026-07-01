#!/usr/bin/env python3
"""WebUI 集成验证测试

验证 DeepAgent WebUI 目录结构、脚本可用性、
品牌替换状态和整体集成情况。
"""

import os
import sys
import subprocess
from pathlib import Path

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 测试 1: webui/ 目录存在且结构完整
# ============================================================
def test_webui_directory_exists():
    """验证 webui/ 目录存在"""
    webui_dir = PROJECT_ROOT / "webui"
    assert webui_dir.exists(), "webui/ 目录不存在"
    assert webui_dir.is_dir(), "webui/ 不是目录"


def test_webui_directory_structure():
    """验证 webui/ 目录包含关键子目录和文件"""
    webui_dir = PROJECT_ROOT / "webui"
    
    # 关键子目录
    expected_dirs = ["bin", "scripts"]
    for d in expected_dirs:
        dir_path = webui_dir / d
        assert dir_path.exists(), f"关键子目录缺失: {d}/"
    
    # 关键文件
    expected_files = [
        "package.json",
        "DEEPAGENT-README.md",
        "README.md",
        "ARCHITECTURE.md",
    ]
    for f in expected_files:
        file_path = webui_dir / f
        assert file_path.exists(), f"关键文件缺失: {f}"


# ============================================================
# 测试 2: setup-webui.sh 脚本语法正确
# ============================================================
def test_setup_webui_sh_syntax():
    """验证 setup-webui.sh 脚本语法正确（bash -n）"""
    script_path = PROJECT_ROOT / "scripts" / "setup-webui.sh"
    assert script_path.exists(), f"setup-webui.sh 不存在: {script_path}"
    
    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode != 0:
        pytest.fail(f"setup-webui.sh 语法错误:\n{result.stderr}")
    
    # 验证脚本包含 DeepAgent 品牌相关关键内容
    content = script_path.read_text(encoding="utf-8")
    assert "DeepAgent" in content, "setup-webui.sh 应包含 DeepAgent 品牌标识"
    assert "webui" in content.lower(), "setup-webui.sh 应引用 webui"


# ============================================================
# 测试 3: start-webui.sh 语法正确且包含 status 逻辑
# ============================================================
def test_start_webui_sh_syntax():
    """验证 start-webui.sh 脚本语法正确（bash -n）"""
    script_path = PROJECT_ROOT / "scripts" / "start-webui.sh"
    assert script_path.exists(), f"start-webui.sh 不存在: {script_path}"
    
    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        capture_output=True, text=True, timeout=10
    )
    
    if result.returncode != 0:
        pytest.fail(f"start-webui.sh 语法错误:\n{result.stderr}")


def test_start_webui_sh_has_status_command():
    """验证 start-webui.sh 包含 status 子命令"""
    script_path = PROJECT_ROOT / "scripts" / "start-webui.sh"
    content = script_path.read_text(encoding="utf-8")
    
    assert "status" in content, "start-webui.sh 应支持 status 子命令"
    assert "help" in content or "usage" in content.lower(), \
        "start-webui.sh 应支持 help/usage 显示"
    
    # 验证 status 函数定义
    assert "cmd_status" in content or "status)" in content, \
        "start-webui.sh 应包含 cmd_status() 函数或 status 分支"


def test_start_webui_sh_help_output():
    """验证 start-webui.sh help 输出格式正确"""
    script_path = PROJECT_ROOT / "scripts" / "start-webui.sh"
    
    result = subprocess.run(
        ["bash", str(script_path), "help"],
        capture_output=True, text=True, timeout=10
    )
    
    assert result.returncode == 0, f"start-webui.sh help 执行失败:\n{result.stderr}"
    
    # 帮助输出应包含关键信息
    output = result.stdout
    assert "DeepAgent" in output or "WebUI" in output, \
        "help 输出应包含 'WebUI' 或 'DeepAgent'"
    assert any(cmd in output for cmd in ["start", "stop", "status"]), \
        "help 输出应列出 start/stop/status 子命令"


# ============================================================
# 测试 4: DEEPAGENT-README.md 存在并包含品牌信息
# ============================================================
def test_deepagent_readme_exists():
    """验证 DEEPAGENT-README.md 存在"""
    readme_path = PROJECT_ROOT / "webui" / "DEEPAGENT-README.md"
    assert readme_path.exists(), "DEEPAGENT-README.md 不存在"
    
    content = readme_path.read_text(encoding="utf-8")
    assert len(content) > 0, "DEEPAGENT-README.md 不应为空"
    
    # 应包含 Deep Agent 品牌内容
    assert "Deep Agent" in content or "DeepAgent" in content, \
        "DEEPAGENT-README.md 应包含 'Deep Agent' 或 'DeepAgent'"


# ============================================================
# 测试 5: deepagent webui 子命令可用
# ============================================================
def test_deepagent_script_has_webui_subcommand():
    """验证 deepagent 启动脚本支持 webui 子命令"""
    deepagent_path = PROJECT_ROOT / "deepagent"
    assert deepagent_path.exists(), "deepagent 启动脚本不存在"
    assert os.access(str(deepagent_path), os.X_OK), "deepagent 启动脚本不可执行"
    
    # 验证脚本包含 webui 子命令处理逻辑
    content = deepagent_path.read_text(encoding="utf-8")
    assert "webui" in content, "deepagent 脚本应包含 webui 子命令处理"
    assert "cmd_webui" in content, "deepagent 脚本应包含 cmd_webui 函数"
    assert "start-webui.sh" in content, \
        "deepagent 脚本应引用 start-webui.sh"


def test_deepagent_webui_help():
    """验证 deepagent webui 帮助信息"""
    deepagent_path = PROJECT_ROOT / "deepagent"
    
    # 模拟 deepagent webui help 调用（不用实际启动）
    result = subprocess.run(
        [sys.executable, str(deepagent_path), "webui", "help"],
        capture_output=True, text=True, timeout=10
    )
    
    # 应能正常输出帮助信息（退出码可能为 0 或非零取决于实现）
    output = (result.stdout + result.stderr)
    assert "WebUI" in output or "webui" in output.lower(), \
        "webui help 输出应包含 'WebUI'"
    assert any(cmd in output for cmd in ["start", "stop", "status"]), \
        "webui help 应列出 start/stop/status"


# ============================================================
# 测试 6: WebUI 的 package.json 存在并含关键元数据
# ============================================================
def test_webui_package_json_exists():
    """验证 webui/package.json 存在并包含关键信息"""
    package_json_path = PROJECT_ROOT / "webui" / "package.json"
    assert package_json_path.exists(), "webui/package.json 不存在"
    
    import json
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"webui/package.json 不是有效的 JSON: {e}")
    
    # 应包含必要字段
    assert "name" in data, "package.json 缺少 name 字段"
    assert "version" in data, "package.json 缺少 version 字段"
    assert data["version"], "package.json version 不应为空"
