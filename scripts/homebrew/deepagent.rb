# ============================================================================
# DeepAgent Homebrew Formula
# ============================================================================
# 安装方式:
#   brew tap yuanchenglu/deepagent https://github.com/yuanchenglu/deepseekagent
#   brew install deepagent
#
# 本地测试:
#   brew install --formula ./scripts/homebrew/deepagent.rb
#   brew test deepagent
#   brew audit --new-formula ./scripts/homebrew/deepagent.rb
#
# 说明:
#   - tarball 为纯 Python 包，无编译扩展，故 bottle :unneeded
#   - 双架构支持：embedded/opencode/ 下包含 macos-arm64 和 macos-x64 二进制
#   - 安装后 deepagent 命令在 PATH 中可用
# ============================================================================
class Deepagent < Formula
  desc "The self-improving AI agent — creates skills from experience, improves them during use, and runs anywhere"
  homepage "https://deepseekagent.starseas.org"
  url "https://deepseekagent.starseas.org/releases/deepagent-0.9.0-alpha.1.tar.gz"
  mirror "https://github.com/yuanchenglu/deepseekagent/releases/download/v0.9.0-alpha.1/deepagent-0.9.0-alpha.1.tar.gz"
  sha256 "d8c29dccbe221bdac3d3dc28fb0af4d4ae418092381bde7e1572a00da0ed849b"
  license "MIT"
  version "0.9.0-alpha.1"

  # 纯 Python tarball，无编译扩展，不需要 bottle
  bottle :unneeded

  # ---- 架构支持 ----
  # tarball 包含预构建的 embedded opencode 二进制，
  # 同时支持 arm64（Apple Silicon）和 x86_64（Intel），
  # 因此同一个 formula 在两种 macOS 架构上均可使用。
  on_macos do
    on_arm do
      # Apple Silicon (arm64): 运行时自动选择 embedded/opencode/macos-arm64/opencode
    end

    on_intel do
      # Intel (x86_64): 运行时自动选择 embedded/opencode/macos-x64/opencode
    end
  end

  # ---- 依赖声明 ----
  depends_on "python@3.12"
  depends_on "uv"
  depends_on "node@23"

  # ---- 安装步骤 ----
  def install
    # 将整个应用目录树放置在 libexec 下，
    # 这样 Homebrew 的 prefix 不会干扰虚拟环境布局。
    libexec.install Dir["*"]

    python3 = Formula["python@3.12"].opt_bin/"python3.12"
    uv = Formula["uv"].opt_bin/"uv"

    cd libexec do
      # 使用 Homebrew 的 python@3.12 创建虚拟环境，
      # 从 uv.lock 安装所有运行时依赖以确保可复现性。
      system uv, "venv", "--python", python3, ".venv"
      system uv, "sync", "--no-dev", "--python", python3
    end

    # 将入口脚本链接到 Homebrew 的 bin 目录，
    # 并设置环境变量指向 Homebrew 管理的配置和 skills 目录，
    # 而非 ~/.deepagent（避免 Homebrew 安装与用户本地安装冲突）。
    env = {
      DEEPAGENT_HOME:           etc/"deepagent",
      DEEPAGENT_BUNDLED_SKILLS: opt_pkgshare/"skills",
    }

    %w[deepagent deepagent-agent deepagent-acp].each do |cmd|
      (bin/cmd).write_env_script libexec/".venv/bin/#{cmd}", env
    end

    # 将内置 skills 安装到 pkgshare，升级时不会覆盖
    # ~/.deepagent/skills/ 下的用户自定义内容。
    if (libexec/"skills").directory?
      rm_rf(pkgshare/"skills")
      (pkgshare/"skills").install Dir[libexec/"skills/*"]
    end

    # 安装预构建的 WebUI 资源。
    (pkgshare/"webui").install Dir[libexec/"webui/*"] if (libexec/"webui").directory?
  end

  def post_install
    # 首次安装或升级时确保配置目录存在。
    (etc/"deepagent").mkpath
  end

  def caveats
    <<~EOS
      配置、会话和 skills 存储在:
        #{etc/"deepagent"}

      启动 WebUI 工作台:
        deepagent webui start

      默认 WebUI 地址: http://localhost:8648
    EOS
  end

  test do
    # 冒烟测试：验证二进制可执行并报告正确版本。
    assert_match version.to_s, shell_output("#{bin}/deepagent --version")
  end
end
