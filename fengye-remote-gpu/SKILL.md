---
name: fengye-remote-gpu
description: "配置、验证和排查 fengye 的局域网 Windows/WSL2/NVIDIA GPU 训练机。用户想从 Mac SSH 到 summerPC、配置 Windows OpenSSH、修复局域网 SSH 超时、配置 SSH key、检查 WSL2 Ubuntu、验证 NVIDIA GPU、准备 PyTorch/CUDA 训练环境、或沉淀本地远程 GPU 工作流时使用。"
---

# fengye-remote-gpu

帮助 fengye 把一台 Windows + WSL2 + NVIDIA GPU 台式机当成本地局域网训练机使用，并从 Mac 或其它本地电脑远程连接。

这个 skill 只处理环境配置和运行检查，不用于完成课程作业。它尤其适合 CS336 学习基础设施：后面需要更重的 PyTorch 实验时，可以把训练任务放到这台 GPU 机器上跑。

## 当前已知配置

截至 2026-07-04，已经打通的配置是：

- Windows 主机名：`summerPC`
- Windows 用户：`summerpc\11291`
- 局域网 IPv4：`192.168.31.234`
- Mac 侧 SSH 别名：`summerpc`
- Mac 侧 SSH 私钥：`~/.ssh/summerpc_cs336_ed25519`
- Mac 侧 SSH 公钥：`~/.ssh/summerpc_cs336_ed25519.pub`
- WSL 发行版：`Ubuntu`
- WSL 版本：WSL2，Ubuntu 24.04.1 LTS
- GPU：NVIDIA GeForce RTX 4080 SUPER，16376 MiB
- 已验证的远程 GPU 检查命令：
  ```bash
  ssh summerpc "wsl -d Ubuntu -e /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"
  ```

预期输出形态：

```text
NVIDIA GeForce RTX 4080 SUPER, <driver_version>, 16376 MiB
```

## 安全规则

- 不要展示或打印私钥内容。公钥可以在安装时展示。
- 修改配置前优先做非破坏性检查。
- 固定局域网 IP 时优先使用路由器 DHCP 地址保留。除非用户明确要求，不要直接修改 Windows 静态 IP。
- 除非用户明确要求，不要重装 WSL、NVIDIA 驱动、CUDA 或大型依赖。
- 如果当前上下文是课程仓库，把环境配置和 assignment 实现严格分开。

## Mac 侧快速检查

从 Mac 或本地控制机运行：

```bash
ping -c 2 192.168.31.234
nc -vz -G 5 192.168.31.234 22
ssh -o BatchMode=yes summerpc "hostname"
ssh -o BatchMode=yes summerpc "whoami"
ssh -o BatchMode=yes summerpc "wsl -d Ubuntu -e uname -a"
ssh -o BatchMode=yes summerpc "wsl -d Ubuntu -e /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"
```

结果判断：

- `ping` 失败：检查局域网、IP 地址、Wi-Fi/以太网、路由器隔离，或者台式机是否睡眠。
- `ping` 成功但 `nc` 超时：通常是 Windows 防火墙 profile、第三方安全软件，或 TCP 22 入站被拦。
- `nc` 成功但 `ssh` 返回 `Permission denied`：网络已经通了，问题在密码或 key 认证。
- `ssh summerpc hostname` 成功：SSH key 免密登录已经可用。
- WSL 的 `uname` 成功但普通 `nvidia-smi` 失败：尝试 `/usr/lib/wsl/lib/nvidia-smi`。非交互 WSL 命令的 PATH 里可能没有 `nvidia-smi`。

## Mac 侧 SSH 配置

`~/.ssh/config` 里应该有这个别名：

```sshconfig
Host summerpc
  HostName 192.168.31.234
  User 11291
  IdentityFile ~/.ssh/summerpc_cs336_ed25519
  IdentitiesOnly yes
```

如果 key 不存在，创建一把专用 key：

```bash
ssh-keygen -t ed25519 -f ~/.ssh/summerpc_cs336_ed25519 -C "fengye@mac-to-summerpc-cs336" -N ""
chmod 600 ~/.ssh/summerpc_cs336_ed25519 ~/.ssh/config
chmod 644 ~/.ssh/summerpc_cs336_ed25519.pub
```

然后把公钥安装到 Windows。

## Windows OpenSSH 检查清单

在 Windows 的管理员 PowerShell 里运行：

```powershell
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'
Get-Service sshd
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
netstat -ano | findstr ":22"
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP*" | Format-Table Name,Enabled,Direction,Action,Profile -AutoSize
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP*" | Get-NetFirewallPortFilter
Get-NetConnectionProfile
```

如果 OpenSSH Server 没安装：

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

## Public 网络下的防火墙修复

2026-07-04 实际遇到的问题：

- Windows 当前网络 `fengye404` 被识别成 `Public`
- 已有规则 `OpenSSH-Server-In-TCP` 只允许 `Private`
- Mac 可以 ping 到 Windows，但 TCP 22 超时

两个有效修法：

方案 A：如果这是可信局域网，把网络改成 Private：

```powershell
Set-NetConnectionProfile -Name "fengye404" -NetworkCategory Private
```

方案 B：新增一条对任意 profile 生效的 SSH 放行规则：

```powershell
New-NetFirewallRule -Name "OpenSSH-Server-In-TCP-Any" -DisplayName "OpenSSH Server TCP 22 Any Profile" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -Profile Any
```

验证：

```powershell
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP*" | Format-Table Name,Enabled,Direction,Action,Profile -AutoSize
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP*" | Get-NetFirewallPortFilter
```

## 在 Windows 上安装 Mac 公钥

普通 Windows 用户的 key 文件：

```text
C:\Users\11291\.ssh\authorized_keys
```

如果 Windows OpenSSH 配置里有：

```text
Match Group administrators
AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
```

还要把同一把公钥写入：

```text
C:\ProgramData\ssh\administrators_authorized_keys
```

普通用户文件的 PowerShell 辅助脚本：

```powershell
$pub = '<paste public key here>'

$sshDir = Join-Path $env:USERPROFILE ".ssh"
$authFile = Join-Path $sshDir "authorized_keys"

New-Item -ItemType Directory -Force -Path $sshDir | Out-Null

if (!(Test-Path $authFile) -or !(Select-String -Path $authFile -SimpleMatch $pub -Quiet)) {
  Add-Content -Path $authFile -Value $pub -Encoding ascii
}

$me = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

icacls $sshDir /inheritance:r | Out-Null
icacls $sshDir /grant "$($me):(OI)(CI)F" | Out-Null

icacls $authFile /inheritance:r | Out-Null
icacls $authFile /grant "$($me):F" | Out-Null

Restart-Service sshd
```

`administrators_authorized_keys` 要设置严格权限：

```powershell
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /grant "NT AUTHORITY\SYSTEM:F" "BUILTIN\Administrators:F"
Restart-Service sshd
```

## WSL 和 GPU 检查

通过 SSH 运行：

```bash
ssh summerpc "wsl -l -v"
ssh summerpc "wsl -d Ubuntu -e cat /etc/os-release"
ssh summerpc "wsl -d Ubuntu -e /usr/lib/wsl/lib/nvidia-smi"
```

检查 WSL 内工具：

```bash
ssh summerpc "wsl -d Ubuntu -e python3 --version"
ssh summerpc "wsl -d Ubuntu -e pip3 --version"
ssh summerpc "wsl -d Ubuntu -e git --version"
ssh summerpc "wsl -d Ubuntu -e nvcc --version"
ssh summerpc "wsl -d Ubuntu -e python3 -c \"import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')\""
```

2026-07-04 的已知状态：

- `python3`：已安装
- `pip3`：已安装
- `git`：已安装
- `nvcc`：已安装，CUDA compiler release 12.0
- `uv`：未安装
- `conda`：未安装
- `torch`：未安装

## 后续 PyTorch 环境建议

用户准备在 GPU 机器上跑 CS336 实验时，在 WSL Ubuntu 里创建隔离环境。优先使用项目本地 `venv` 或 `uv` 环境。除非用户明确偏好，不要把 PyTorch 全局安装到系统 Python。

安装 PyTorch 前，先查看官方安装选择器，因为 PyTorch/CUDA 包推荐会变化。

## 汇报模板

汇报状态时使用这个结构：

```text
SSH:
- 局域网可达:
- TCP 22:
- key 免密:

Windows:
- 主机/用户:
- sshd:
- 防火墙规则:

WSL/GPU:
- 发行版:
- GPU 可见:
- PyTorch CUDA:

下一步:
- ...
```
