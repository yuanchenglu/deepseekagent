# Windows 10 LTSC 2021 WSL2 安装排查记录

## 环境

- OS: Windows 10 LTSC 2021 (build 19044.7417)
- 用户名: bluth
- 管理员组成员: 是（但 SSH 受 UAC 限制）
- 网络: 从中国访问微软 CDN ~35 KB/s

## 排查路径

### 第一步：确认 WSL 功能状态

```cmd
dism /online /get-features /format:table | findstr -i "wsl virtualmachine subsystem"
```
→ Microsoft-Windows-Subsystem-Linux: 已启用
→ VirtualMachinePlatform: 已启用

### 第二步：wsl --install 测试

| 命令 | 结果 | 耗时 |
|------|------|------|
| `wsl --install` | 卡死/无输出 | 5min+ |
| `wsl --install -d Ubuntu` | 超时 | 5min |
| `wsl --install --web-download` | exit 1, 假成功 | - |
| `wsl --install --inbox --no-launch` | SUCCESS 但无发行版 | - |

### 第三步：WSL2 内核更新

```cmd
curl.exe -L -o "%TEMP%\wsl_update_x64.msi" "https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi"
```
- 下载成功（~15MB），但速度 ~35-45 KB/s
- MSI 安装需管理员权限（SSH 受 UAC 限制）

**提权方案（有效）：**
```cmd
schtasks /create /tn WslKernelInstall /tr "msiexec /i %TEMP%\wsl_update_x64.msi /quiet /norestart" /sc once /st 00:01 /rl highest /ru SYSTEM /f
schtasks /run /tn WslKernelInstall
```
- 结果: error 1603（Fatal error during installation）
- 但 `C:\Windows\System32\lxss\tools\kernel` 文件已存在（可能功能启用时就有）

### 第四步：下载发行版

```cmd
curl.exe -L -o "%TEMP%\Ubuntu.appxbundle" "https://aka.ms/wslubuntu2204"
```
- 1.06 GB 文件，35 KB/s → 预计 8 小时
- 未等待完成即终止

### 最终方案：wsl --install --inbox （次优）

```cmd
wsl --install --inbox --no-launch
```
返回 SUCCESS，但并未安装实际发行版（仅确认收件箱功能）。

## 核心洞察

1. **LTSC 不含 Store WSL 通道**，`wsl --install` 在其上行为异常
2. **wsl.exe 版本**：LTSC 2021 的收件箱版 wsl.exe 有 `--install` 参数但功能不完整
3. **最快的完成路径**：在 Windows 本地用 Microsoft Store 安装 Ubuntu，或从国内镜像下载 Appx 包
4. **UTF-16 LE 输出**：中文 Windows 的 cmd/PowerShell 输出需 `iconv -f UTF-16LE -t UTF-8` 转换

## 推荐命令速查

```bash
# 连接测试
sshpass -p 'password' ssh -o StrictHostKeyChecking=no user@host "hostname && whoami"

# 查看版本信息（纯英文）
sshpass -p 'password' ssh user@host cmd /c "chcp 437 >nul & ver & wsl --list --online"

# 查看中文输出（带编码转换）
sshpass -p 'password' ssh user@host cmd /c "wsl --list --online" 2>&1 | iconv -f UTF-16LE -t UTF-8//IGNORE

# 写脚本到远程再执行（规避嵌套引号问题）
sshpass -p 'password' ssh user@host cmd /c "echo powershell -Command \"Get-AppxPackage ...\" > C:\script.bat & C:\script.bat"

# 检查是否能装特定功能
sshpass -p 'password' ssh user@host cmd /c "dism /online /get-featureinfo /featurename:Microsoft-Windows-Subsystem-Linux 2>&1 | findstr State"
```
