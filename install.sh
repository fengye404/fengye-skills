#!/bin/bash
# fengye-skills 安装脚本
# 将所有 skills 通过软链接同步到各个 AI 工具

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 当前仓库路径（脚本所在目录）
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 获取所有 skill 目录
get_skills() {
  ls -d "$REPO_DIR"/*/ 2>/dev/null | xargs -n1 basename | grep -v "\.git"
}

# 创建软链接的通用函数
link_skill() {
  local target_dir="$1"
  local skill_name="$2"
  local source_path="$REPO_DIR/$skill_name"
  local target_path="$target_dir/$skill_name"

  # 如果目标已存在且不是软链接，备份它
  if [ -e "$target_path" ] && [ ! -L "$target_path" ]; then
    echo -e "${YELLOW}备份已存在的 $skill_name${NC}"
    mv "$target_path" "$target_path.backup.$(date +%Y%m%d_%H%M%S)"
  fi

  # 如果软链接已存在，先删除
  if [ -L "$target_path" ]; then
    rm "$target_path"
  fi

  # 创建软链接
  ln -s "$source_path" "$target_path"
  echo -e "${GREEN}✓${NC} $skill_name"
}

# 安装到 Claude Code
install_claude() {
  echo -e "\n${BLUE}=== Claude Code ===${NC}"
  local target="$HOME/.claude/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 .agents/skills（通用目录）
install_agents() {
  echo -e "\n${BLUE}=== Universal Agents ===${NC}"
  local target="$HOME/.agents/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 Trae
install_trae() {
  echo -e "\n${BLUE}=== Trae ===${NC}"
  local target="$HOME/.trae/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 Trae CN
install_trae_cn() {
  echo -e "\n${BLUE}=== Trae CN ===${NC}"
  local target="$HOME/.trae-cn/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 Gemini CLI
install_gemini() {
  echo -e "\n${BLUE}=== Gemini CLI ===${NC}"
  local target="$HOME/.gemini/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 Qoder
install_qoder() {
  echo -e "\n${BLUE}=== Qoder ===${NC}"
  local target="$HOME/.qoder/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 Continue
install_continue() {
  echo -e "\n${BLUE}=== Continue ===${NC}"
  local target="$HOME/.continue/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 Codex
install_codex() {
  echo -e "\n${BLUE}=== Codex ===${NC}"
  local target="$HOME/.codex/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 OpenClaw
install_openclaw() {
  echo -e "\n${BLUE}=== OpenClaw ===${NC}"
  local target="$HOME/.openclaw/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 安装到 OpenCode
install_opencode() {
  echo -e "\n${BLUE}=== OpenCode ===${NC}"
  local target="$HOME/.config/opencode/skills"
  mkdir -p "$target"

  for skill in $(get_skills); do
    link_skill "$target" "$skill"
  done
}

# 显示帮助
show_help() {
  cat << EOF
fengye-skills 安装脚本

用法: $0 [命令] [选项]

命令:
  all         安装到所有支持的 AI 工具（默认）
  claude      仅安装到 Claude Code
  agents      仅安装到 Universal Agents
  trae        仅安装到 Trae
  trae-cn     仅安装到 Trae CN
  gemini      仅安装到 Gemini CLI
  qoder       仅安装到 Qoder
  continue    仅安装到 Continue
  codex       仅安装到 Codex
  openclaw    仅安装到 OpenClaw
  opencode    仅安装到 OpenCode
  list        列出当前所有 skills
  status      对比 lock 文件，显示哪些 skill 有变更
  help        显示此帮助信息

示例:
  $0              # 安装到所有工具
  $0 claude       # 仅安装到 Claude Code
  $0 list         # 列出所有 skills

EOF
}

# 列出所有 skills
list_skills() {
  echo -e "${BLUE}当前仓库中的 skills:${NC}\n"
  for skill in $(get_skills); do
    local skill_file="$REPO_DIR/$skill/SKILL.md"
    local claude_file="$REPO_DIR/$skill/CLAUDE.md"

    if [ -f "$skill_file" ]; then
      local desc=$(grep -m1 "^description:" "$skill_file" 2>/dev/null | cut -d: -f2- | xargs)
      echo -e "${GREEN}•${NC} $skill${desc:+ - $desc}"
    elif [ -f "$claude_file" ]; then
      local title=$(grep -m1 "^# " "$claude_file" 2>/dev/null | cut -d' ' -f2-)
      echo -e "${GREEN}•${NC} $skill${title:+ - $title}"
    else
      echo -e "${GREEN}•${NC} $skill"
    fi
  done
  echo -e "\n共 $(get_skills | wc -l) 个 skills"
}

# 计算单个 skill 的哈希
compute_skill_hash() {
  local skill_dir="$1"
  python3 << PYEOF
import os, hashlib
skill_dir = "$skill_dir"
file_hashes = []
for root, dirs, files in os.walk(skill_dir):
    for f in sorted(files):
        if f in ('.DS_Store', '.query_id_cache.json'):
            continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, skill_dir)
        with open(fp, 'rb') as fh:
            h = hashlib.sha256(rel.encode() + fh.read()).hexdigest()
        file_hashes.append(h)
print(hashlib.sha256(''.join(sorted(file_hashes)).encode()).hexdigest())
PYEOF
}

# 从 lock 文件读取某个 skill 的旧哈希
get_locked_hash() {
  local skill="$1"
  local lock_file="$REPO_DIR/skills-lock.json"
  if [ -f "$lock_file" ]; then
    python3 -c "
import json
with open('$lock_file') as f:
    data = json.load(f)
print(data.get('skills', {}).get('$skill', {}).get('hash', ''))
" 2>/dev/null
  fi
}

# 对比 lock 文件，显示变更摘要
diff_lock() {
  local lock_file="$REPO_DIR/skills-lock.json"
  local new_skills=()
  local changed_skills=()
  local unchanged_skills=()

  if [ ! -f "$lock_file" ]; then
    echo -e "\n${YELLOW}首次安装，跳过变更检测${NC}"
    return
  fi

  # 检查已删除的 skill
  local old_skills=$(python3 -c "
import json
with open('$lock_file') as f:
    data = json.load(f)
for s in sorted(data.get('skills', {}).keys()):
    print(s)
" 2>/dev/null)

  local current_skills=$(get_skills | sort)

  for skill in $current_skills; do
    local old_hash=$(get_locked_hash "$skill")
    if [ -z "$old_hash" ]; then
      new_skills+=("$skill")
    else
      local new_hash=$(compute_skill_hash "$REPO_DIR/$skill")
      if [ "$old_hash" != "$new_hash" ]; then
        changed_skills+=("$skill")
      else
        unchanged_skills+=("$skill")
      fi
    fi
  done

  local deleted_skills=()
  for skill in $old_skills; do
    if ! echo "$current_skills" | grep -qw "$skill"; then
      deleted_skills+=("$skill")
    fi
  done

  echo -e "\n${BLUE}=== 变更摘要 ===${NC}"

  if [ ${#new_skills[@]} -gt 0 ]; then
    for s in "${new_skills[@]}"; do
      echo -e "  ${GREEN}+ 新增${NC} $s"
    done
  fi
  if [ ${#changed_skills[@]} -gt 0 ]; then
    for s in "${changed_skills[@]}"; do
      echo -e "  ${YELLOW}~ 变更${NC} $s"
    done
  fi
  if [ ${#deleted_skills[@]} -gt 0 ]; then
    for s in "${deleted_skills[@]}"; do
      echo -e "  ${RED}- 删除${NC} $s"
    done
  fi
  if [ ${#unchanged_skills[@]} -gt 0 ]; then
    echo -e "  ${NC}  未变 ${#unchanged_skills[@]} 个 skill${NC}"
  fi

  local total_changes=$(( ${#new_skills[@]} + ${#changed_skills[@]} + ${#deleted_skills[@]} ))
  if [ "$total_changes" -eq 0 ]; then
    echo -e "  ${NC}无变更${NC}"
  fi
}

# 生成 skills-lock.json
generate_lock() {
  local lock_file="$REPO_DIR/skills-lock.json"

  python3 << PYEOF
import json, os, hashlib, subprocess, re
from pathlib import Path

repo = "$REPO_DIR"
skills = {}

for d in sorted(os.listdir(repo)):
    skill_dir = os.path.join(repo, d)
    if not os.path.isdir(skill_dir) or d.startswith('.'):
        continue
    skill_md = os.path.join(skill_dir, 'SKILL.md')
    claude_md = os.path.join(skill_dir, 'CLAUDE.md')
    if not os.path.exists(skill_md) and not os.path.exists(claude_md):
        continue

    # Compute hash
    file_hashes = []
    file_count = 0
    for root, dirs, files in os.walk(skill_dir):
        for f in sorted(files):
            if f in ('.DS_Store', '.query_id_cache.json'):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, skill_dir)
            with open(fp, 'rb') as fh:
                h = hashlib.sha256(rel.encode() + fh.read()).hexdigest()
            file_hashes.append(h)
            file_count += 1
    combined = hashlib.sha256(''.join(sorted(file_hashes)).encode()).hexdigest()

    # Extract description
    desc = ""
    if os.path.exists(skill_md):
        with open(skill_md) as f:
            for line in f:
                line = line.strip()
                if line.startswith('description:'):
                    desc = line.split(':', 1)[1].strip().strip('"').strip("'")
                    break

    skills[d] = {"hash": combined, "files": file_count, "description": desc}

lock = {"version": 1, "skills": skills}
with open("$lock_file", 'w') as f:
    json.dump(lock, f, indent=2, ensure_ascii=False)
    f.write('\n')
PYEOF

  echo -e "\n${GREEN}✓${NC} skills-lock.json 已更新"
}

# 主逻辑
main() {
  local command="${1:-all}"

  case "$command" in
    all)
      install_claude
      install_agents
      install_trae
      install_trae_cn
      install_gemini
      install_qoder
      install_continue
      install_codex
      install_openclaw
      install_opencode
      diff_lock
      generate_lock
      echo -e "\n${GREEN}✓ 所有 skills 已同步到各 AI 工具${NC}"
      ;;
    claude)      install_claude ;;
    agents)      install_agents ;;
    trae)        install_trae ;;
    trae-cn)     install_trae_cn ;;
    gemini)      install_gemini ;;
    qoder)       install_qoder ;;
    continue)    install_continue ;;
    codex)       install_codex ;;
    openclaw)    install_openclaw ;;
    opencode)    install_opencode ;;
    list)        list_skills ;;
    status)      diff_lock ;;
    help|--help|-h) show_help ;;
    *)
      echo -e "${RED}未知命令: $command${NC}"
      show_help
      exit 1
      ;;
  esac
}

main "$@"
