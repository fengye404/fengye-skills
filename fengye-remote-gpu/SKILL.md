---
name: fengye-remote-gpu
description: "Set up, verify, and troubleshoot Fengye's LAN Windows/WSL2 NVIDIA GPU training machine from a Mac or another local computer. Use this when the user wants to SSH into summerPC, configure Windows OpenSSH, fix LAN SSH timeouts, set up SSH keys, check WSL2 Ubuntu, verify NVIDIA GPU visibility, prepare a PyTorch/CUDA training environment, or document the local remote-GPU workflow."
---

# fengye-remote-gpu

Help Fengye use a Windows + WSL2 + NVIDIA GPU desktop as a local LAN training machine from a Mac or another computer.

This skill is for environment setup and operational checks, not for solving course assignments. It is especially useful for CS336 study infrastructure, where the GPU box can run heavier PyTorch experiments later.

## Known Current Setup

As of 2026-07-04, the working machine is:

- Windows host: `summerPC`
- Windows user: `summerpc\11291`
- LAN IPv4: `192.168.31.234`
- Mac SSH alias: `summerpc`
- Mac SSH private key: `~/.ssh/summerpc_cs336_ed25519`
- Mac SSH public key: `~/.ssh/summerpc_cs336_ed25519.pub`
- WSL distro: `Ubuntu`
- WSL version: WSL2, Ubuntu 24.04.1 LTS
- GPU: NVIDIA GeForce RTX 4080 SUPER, 16376 MiB
- Verified remote GPU command:
  ```bash
  ssh summerpc "wsl -d Ubuntu -e /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"
  ```

Expected verified output shape:

```text
NVIDIA GeForce RTX 4080 SUPER, <driver_version>, 16376 MiB
```

## Safety Rules

- Do not reveal or print private key contents. Public keys are okay to display when installing them.
- Prefer non-destructive checks before making changes.
- Prefer router DHCP reservation for a stable LAN IPv4 address. Do not change Windows static IP unless the user explicitly wants that.
- Do not reinstall WSL, NVIDIA drivers, CUDA, or large packages unless the user explicitly asks.
- If the task is for a course repository, keep environment setup separate from assignment implementation.

## Fast Status Check From Mac

Run these from the Mac or local control machine:

```bash
ping -c 2 192.168.31.234
nc -vz -G 5 192.168.31.234 22
ssh -o BatchMode=yes summerpc "hostname"
ssh -o BatchMode=yes summerpc "whoami"
ssh -o BatchMode=yes summerpc "wsl -d Ubuntu -e uname -a"
ssh -o BatchMode=yes summerpc "wsl -d Ubuntu -e /usr/lib/wsl/lib/nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader"
```

Interpretation:

- `ping` fails: check LAN, IP address, Wi-Fi/Ethernet, router isolation, or whether the desktop is asleep.
- `ping` works but `nc` times out: Windows firewall/profile/third-party security software is likely blocking TCP 22.
- `nc` works but `ssh` says `Permission denied`: network is fine; fix password/key authentication.
- `ssh summerpc hostname` works: SSH key login is ready.
- WSL `uname` works but `nvidia-smi` fails by name: try `/usr/lib/wsl/lib/nvidia-smi`; non-interactive WSL PATH may not include it.

## Mac SSH Configuration

The working SSH alias should look like this in `~/.ssh/config`:

```sshconfig
Host summerpc
  HostName 192.168.31.234
  User 11291
  IdentityFile ~/.ssh/summerpc_cs336_ed25519
  IdentitiesOnly yes
```

If the key does not exist, create a dedicated one:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/summerpc_cs336_ed25519 -C "fengye@mac-to-summerpc-cs336" -N ""
chmod 600 ~/.ssh/summerpc_cs336_ed25519 ~/.ssh/config
chmod 644 ~/.ssh/summerpc_cs336_ed25519.pub
```

Then install the public key on Windows.

## Windows OpenSSH Checklist

Run from an administrator PowerShell on Windows when configuring or debugging:

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

If OpenSSH Server is missing:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

## Firewall Fix For Public Networks

The actual issue found on 2026-07-04:

- Windows network `fengye404` was categorized as `Public`
- Existing rule `OpenSSH-Server-In-TCP` only allowed `Private`
- Mac could ping Windows but TCP 22 timed out

Two valid fixes:

Option A, if the LAN is trusted, change the network to Private:

```powershell
Set-NetConnectionProfile -Name "fengye404" -NetworkCategory Private
```

Option B, add an explicit SSH rule for any profile:

```powershell
New-NetFirewallRule -Name "OpenSSH-Server-In-TCP-Any" -DisplayName "OpenSSH Server TCP 22 Any Profile" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 -Profile Any
```

Verify:

```powershell
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP*" | Format-Table Name,Enabled,Direction,Action,Profile -AutoSize
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP*" | Get-NetFirewallPortFilter
```

## Install The Mac Public Key On Windows

For a normal Windows user, write to:

```text
C:\Users\11291\.ssh\authorized_keys
```

If the Windows OpenSSH config contains:

```text
Match Group administrators
AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
```

also write the same public key to:

```text
C:\ProgramData\ssh\administrators_authorized_keys
```

PowerShell helper for the normal user file:

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

For `administrators_authorized_keys`, set tight permissions:

```powershell
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /inheritance:r
icacls "C:\ProgramData\ssh\administrators_authorized_keys" /grant "NT AUTHORITY\SYSTEM:F" "BUILTIN\Administrators:F"
Restart-Service sshd
```

## WSL And GPU Checks

Run through SSH:

```bash
ssh summerpc "wsl -l -v"
ssh summerpc "wsl -d Ubuntu -e cat /etc/os-release"
ssh summerpc "wsl -d Ubuntu -e /usr/lib/wsl/lib/nvidia-smi"
```

Tool checks inside WSL:

```bash
ssh summerpc "wsl -d Ubuntu -e python3 --version"
ssh summerpc "wsl -d Ubuntu -e pip3 --version"
ssh summerpc "wsl -d Ubuntu -e git --version"
ssh summerpc "wsl -d Ubuntu -e nvcc --version"
ssh summerpc "wsl -d Ubuntu -e python3 -c \"import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')\""
```

Known state on 2026-07-04:

- `python3`: installed
- `pip3`: installed
- `git`: installed
- `nvcc`: installed, CUDA compiler release 12.0
- `uv`: not installed
- `conda`: not installed
- `torch`: not installed yet

## Recommended Next Step For PyTorch Work

When the user is ready to run CS336 experiments on the GPU box, set up an isolated environment inside WSL Ubuntu. Prefer a project-local `venv` or `uv` environment. Do not install PyTorch globally unless the user explicitly prefers that.

Before installing PyTorch, check the current official install selector because PyTorch/CUDA package recommendations change over time.

## Summary Template

When reporting status, use this shape:

```text
SSH:
- LAN reachability:
- TCP 22:
- Key login:

Windows:
- Host/user:
- sshd:
- firewall rule:

WSL/GPU:
- distro:
- GPU visible:
- PyTorch CUDA:

Next:
- ...
```
