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

# 生成 skills-lock.json
generate_lock() {
  local lock_file="$REPO_DIR/skills-lock.json"
  local tmp_file="$lock_file.tmp"
  local first=true

  echo '{' > "$tmp_file"
  echo '  "version": 1,' >> "$tmp_file"
  echo '  "skills": {' >> "$tmp_file"

  for skill in $(get_skills | sort); do
    local skill_dir="$REPO_DIR/$skill"

    # 计算 skill 目录的内容哈希（排除 .DS_Store 和缓存文件）
    local hash=$(find "$skill_dir" -type f \
      ! -name '.DS_Store' \
      ! -name '.query_id_cache.json' \
      -exec shasum -a 256 {} \; | sort | shasum -a 256 | cut -d' ' -f1)

    # 统计文件数
    local file_count=$(find "$skill_dir" -type f \
      ! -name '.DS_Store' \
      ! -name '.query_id_cache.json' | wc -l | tr -d ' ')

    # 提取描述
    local desc=""
    if [ -f "$skill_dir/SKILL.md" ]; then
      desc=$(grep -m1 '^description:' "$skill_dir/SKILL.md" 2>/dev/null | sed 's/^description: *//;s/^"//;s/"$//' | head -1)
    fi

    if [ "$first" = true ]; then
      first=false
    else
      echo ',' >> "$tmp_file"
    fi

    # 转义 JSON 字符串中的特殊字符
    desc=$(echo "$desc" | sed 's/\\/\\\\/g; s/"/\\"/g')

    printf '    "%s": {\n' "$skill" >> "$tmp_file"
    printf '      "hash": "%s",\n' "$hash" >> "$tmp_file"
    printf '      "files": %s,\n' "$file_count" >> "$tmp_file"
    printf '      "description": "%s"\n' "$desc" >> "$tmp_file"
    printf '    }' >> "$tmp_file"
  done

  echo '' >> "$tmp_file"
  echo '  }' >> "$tmp_file"
  echo '}' >> "$tmp_file"

  mv "$tmp_file" "$lock_file"
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
    help|--help|-h) show_help ;;
    *)
      echo -e "${RED}未知命令: $command${NC}"
      show_help
      exit 1
      ;;
  esac
}

main "$@"
