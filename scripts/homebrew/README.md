# DeepAgent Homebrew Formula — 本地测试指南

## 文件说明

| 文件 | 说明 |
|------|------|
| `deepagent.rb` | Homebrew Formula 定义文件 |

## 本地测试方法

### 1. 直接安装测试

```bash
# 从 formula 文件直接安装（跳过 tap）
brew install --formula ./scripts/homebrew/deepagent.rb

# 验证安装
deepagent --version

# 卸载
brew uninstall deepagent
```

### 2. 审计测试

```bash
# 审计 formula（检查格式、规范等）
brew audit --new-formula ./scripts/homebrew/deepagent.rb

# 如果需要跳过网络检查
brew audit --new-formula --online ./scripts/homebrew/deepagent.rb
```

### 3. 通过 Tap 测试

```bash
# 创建本地 tap
brew tap-new yuanchenglu/deepagent

# 复制 formula 到 tap 目录
cp scripts/homebrew/deepagent.rb $(brew --repository yuanchenglu/deepagent)/Formula/

# 安装
brew install yuanchenglu/deepagent/deepagent

# 测试
brew test deepagent

# 卸载
brew uninstall yuanchenglu/deepagent/deepagent
brew untap yuanchenglu/deepagent
```

## 发布流程

1. 构建 Release tarball：`bash scripts/build-release.sh --version 0.9.0-alpha.1`
2. 上传到 R2 和 GitHub Releases
3. 计算 tarball 的 SHA256：`shasum -a 256 dist/releases/deepagent-0.9.0-alpha.1.tar.gz`
4. 更新 `deepagent.rb` 中的 `sha256` 值（替换 `PLACEHOLDER_SHA256_WILL_BE_FILLED_DURING_RELEASE`）
5. 创建 Homebrew tap 仓库（如 `yuanchenglu/homebrew-deepagent`）
6. 将 formula 推送到 tap 仓库的 `Formula/` 目录
7. 用户安装：`brew tap yuanchenglu/deepagent && brew install deepagent`

## 依赖说明

- `python@3.12`：运行时 Python 版本
- `uv`：Python 包管理器（用于创建 venv 和安装依赖）
- `node@23`：Node.js（WebUI 和 embedded opencode 需要）
