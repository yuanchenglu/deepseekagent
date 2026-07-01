#!/usr/bin/env python3
"""品牌替换验证测试

验证 brand-replace.py 脚本可正常运行，
并检查项目中 "Hermes" 品牌残留情况。
"""

import importlib.util
import os
import sys
import subprocess
import tempfile
from pathlib import Path

import pytest

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 辅助函数
# ============================================================

def _is_legitimate_reference(file_path: Path, line: str) -> bool:
    """判断一行中的 "Hermes" 引用是否为合法引用（不应被替换的）。
    
    合法引用包括：
    - URL / 链接中包含 "hermes"
    - import 语句中的模块路径（如 hermes_cli, hermes_state）
    - 代码 API / 包名引用
    - 版权声明或许可证中的原始名称
    - 注释说明历史来源（如 "forked from Hermes"）
    """
    lower_line = line.lower()
    
    # URL 引用
    if "http://" in lower_line or "https://" in lower_line:
        # 检查 URL 中是否包含 hermes
        url_start = max(lower_line.find("http://"), lower_line.find("https://"))
        if url_start >= 0 and "hermes" in lower_line[url_start:]:
            return True
    
    # 常见的包/模块路径引用
    legit_modules = [
        "hermes_cli", "hermes_state", "hermes_logging", "hermes_constants",
        "hermes_time", "hermes_", "hermes-web-ui", "hermes-studio",
        "hermes_bridge", "hermes-gateway", "hermes-web",
    ]
    for mod in legit_modules:
        if mod in lower_line:
            return True
    
    # git 操作中的引用
    if lower_line.startswith("from ") or lower_line.startswith("import "):
        if "hermes" in lower_line:
            return True
    
    # 注释中说明 fork 来源
    if "#" in line and ("hermes" in lower_line):
        # 注释中提及 fork、来源、原名等属于合法说明
        if any(w in lower_line for w in ["fork", "原名", "原为", "来源", "original", "from", "hermes agent"]):
            return True
    
    # pyproject.toml 或 setup.cfg 中的包名引用
    if file_path.name in ("pyproject.toml", "setup.cfg", "setup.py", "MANIFEST.in", "Cargo.toml"):
        if "hermes" in lower_line:
            return True

    # package.json 中的 name/description 字段引用原始上游仓库
    if file_path.name == "package.json" and "hermes" in lower_line:
        return True
    
    # .github/ 配置文件或 CI 相关引用
    if ".github" in str(file_path):
        if "hermes" in lower_line:
            return True
    
    # 许可证文件
    if file_path.name in ("LICENSE", "LICENSE.txt", "LICENSE.md", "BSL-1.1"):
        if "hermes" in lower_line:
            return True
    
    return False


# ============================================================
# 测试 1: brand-replace.py 可正常导入
# ============================================================
def test_brand_replace_script_importable():
    """验证 brand-replace.py 脚本可以正常导入（语法正确）"""
    script_path = PROJECT_ROOT / "scripts" / "brand-replace.py"
    assert script_path.exists(), f"brand-replace.py 不存在: {script_path}"
    
    # 使用 importlib 验证脚本可被解析
    spec = importlib.util.spec_from_file_location("brand_replace", str(script_path))
    assert spec is not None, "brand-replace.py 无法被解析为 Python 模块"
    
    mod = importlib.util.module_from_spec(spec)
    # 注意：不执行 main()，只验证加载不报 SyntaxError
    try:
        spec.loader.exec_module(mod)
    except SyntaxError as e:
        pytest.fail(f"brand-replace.py 存在语法错误: {e}")
    
    # 验证模块包含关键函数
    assert hasattr(mod, "main"), "brand-replace.py 缺少 main() 函数"
    assert hasattr(mod, "replace_in_file"), "brand-replace.py 缺少 replace_in_file() 函数"


# ============================================================
# 测试 2: --dry-run 模式不修改文件
# ============================================================
def test_dry_run_does_not_modify_files():
    """验证 --dry-run 模式只预览不修改文件"""
    script_path = PROJECT_ROOT / "scripts" / "brand-replace.py"
    
    # 获取 git 状态基准
    result_before = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    before_lines = set(result_before.stdout.strip().split("\n")) if result_before.stdout.strip() else set()
    
    # 运行 dry-run（默认行为也是 dry-run）
    result = subprocess.run(
        [sys.executable, str(script_path), "--dry-run", "--target=tests/test_brand_replacement.py"],
        capture_output=True, text=True, timeout=30,
        cwd=PROJECT_ROOT
    )
    
    assert result.returncode == 0, f"dry-run 执行失败:\n{result.stderr}"
    
    # 验证输出包含 DRY-RUN 标记
    assert "[DRY-RUN]" in result.stdout, "dry-run 输出应包含 [DRY-RUN] 标记"
    
    # 验证文件没有被修改
    result_after = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    after_lines = set(result_after.stdout.strip().split("\n")) if result_after.stdout.strip() else set()
    
    new_changes = after_lines - before_lines
    assert len(new_changes) == 0, f"dry-run 后不应有新的 git 变更，发现: {new_changes}"


# ============================================================
# 测试 3: 关键 Python 文件不含 "Hermes" 品牌残留
# ============================================================
def test_no_unreplaced_hermes_in_python_source():
    """验证核心 Python 源文件不含未替换的 "Hermes" 品牌残留
    
    排除合法引用：
    - URL 链接
    - import 语句中的模块路径
    - 包名引用
    - 注释说明来源
    """
    # 核心源目录
    core_dirs = [
        PROJECT_ROOT / "deepagent_code_mode",
        PROJECT_ROOT / "deepagent_harness",
        PROJECT_ROOT / "embedded",
    ]
    
    # 也可以添加 scripts/ 中的 Python 文件（除了 hermes-gateway）
    script_files = [
        PROJECT_ROOT / "scripts" / "brand-replace.py",
    ]
    
    # brand-replace.py 本身是品牌替换工具，其中包含 "Hermes" 引用是设计上的合法需要
    # 不做品牌残留检查
    exclude_files = {
        str(PROJECT_ROOT / "scripts" / "brand-replace.py"),
    }
    
    violations = []
    
    for directory in core_dirs:
        if not directory.exists():
            continue
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            if str(py_file) in exclude_files:
                continue
            _check_file_for_hermes(py_file, violations)
    
    for py_file in script_files:
        if py_file.exists():
            if str(py_file) in exclude_files:
                continue
            _check_file_for_hermes(py_file, violations)
    
    if violations:
        msg = "\n".join([f"  {f}:{l} → {line.strip()}" for f, l, line in violations])
        pytest.fail(f"发现未替换的 'Hermes' 品牌残留（排除合法引用）:\n{msg}")


def _check_file_for_hermes(file_path: Path, violations: list):
    """检查单个文件中是否有未替换的 Hermes 引用"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return
    
    for line_num, line in enumerate(content.split("\n"), 1):
        lower = line.lower()
        # 检查 "Hermes"（大小写敏感）/ "hermes" 文字
        if "hermes" in lower:
            # 跳过合法引用
            if _is_legitimate_reference(file_path, line):
                continue
            # 由于 brand-replace.py 会把 "Hermes" 替换为 "DeepAgent"，
            # "hermes" 替换为 "deepagent"，所以检查不应该有 "hermes" 出现
            violations.append((str(file_path), line_num, line))


# ============================================================
# 测试 4: Python 编译检查 — 所有 Python 文件编译不报错
# ============================================================
def test_python_compile_every_module():
    """验证所有核心 Python 模块能通过编译（至少语法正确）"""
    core_dirs = [
        PROJECT_ROOT / "deepagent_code_mode",
        PROJECT_ROOT / "deepagent_harness",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "embedded",
    ]
    
    compile_errors = []
    
    for directory in core_dirs:
        if not directory.exists():
            continue
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                compile(py_file.read_text(encoding="utf-8"), str(py_file), "exec")
            except SyntaxError as e:
                compile_errors.append((str(py_file), str(e)))
    
    if compile_errors:
        msg = "\n".join([f"  {f}: {e}" for f, e in compile_errors])
        pytest.fail(f"以下文件编译失败:\n{msg}")
