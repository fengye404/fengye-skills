# fengye-skills

个人 AI 工具 Skills 的**集中管理仓库**。

## 🎯 设计理念

**一个仓库，管理所有 AI 工具的 Skills。**

本仓库是所有 AI 工具（Claude Code、Cursor、Trae、Gemini CLI 等）skills 的**唯一真实来源**（Single Source of Truth）。所有 skill 的真实文件都存放在此仓库中，本地各 AI 工具的 skills 目录通过**软链接**指向这里。

### 为什么这样设计？

1. **统一管理** - 所有 skills 在一个地方，方便查看、编辑和版本控制
2. **Git 同步** - 推送到 GitHub 后在多台机器间同步
3. **避免重复** - 不用在每个 AI 工具里重复维护相同的 skill 文件
4. **自动分发** - 添加新 skill 时自动同步到所有支持的 AI 工具

## 📦 支持的 AI 工具

| 工具 | Skills 目录 |
|------|------------|
| Claude Code | `~/.claude/skills/` |
| Universal Agents | `~/.agents/skills/` |
| Trae | `~/.trae/skills/` |
| Trae CN | `~/.trae-cn/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| Qoder | `~/.qoder/skills/` |
| Continue | `~/.continue/skills/` |
| Codex | `~/.codex/skills/` |
| OpenClaw | `~/.openclaw/skills/` |
| OpenCode | `~/.config/opencode/skills/` |

## 🚀 快速开始

### 首次安装

克隆仓库后，运行安装脚本建立软链接：

```bash
cd fengye-skills
./install.sh
```

这会将所有 skills 通过软链接同步到所有支持的 AI 工具。

### 安装到指定工具

```bash
./install.sh claude      # 仅 Claude Code
./install.sh trae        # 仅 Trae
./install.sh gemini      # 仅 Gemini CLI
# ... 其他工具
```

## 📁 当前 Skills

| Skill | 描述 |
|-------|------|
| **agent-browser** | 浏览器自动化 CLI，用于网页交互、数据提取等 |
| **autoresearch** | 基于 Karpathy 方法论的 skill 自动优化工具 |
| **copywriting** | 营销文案撰写和优化 |
| **create-readme** | 自动生成项目 README |
| **fengye-blog-style** | fengye404.top 博客写作风格（个人定制化） |
| **find-skills** | 从 skills.sh 生态发现和安装 skills |
| **frontend-design** | mager 风格的前端设计指导 |
| **macos-design-guidelines** | Apple Human Interface Guidelines for Mac |
| **skill-creator** | 创建自定义 Claude Code skills 的工具（含评测功能） |
| **typescript-expert** | TypeScript/JavaScript 专家级指导 |
| **ui-ux-pro-max** | UI/UX 设计智能，50+ 风格、配色、字体组合 |
| **web-design-guidelines** | Web 界面设计规范审查 |
| **webapp-testing** | 使用 Playwright 测试本地 Web 应用 |

查看完整列表：
```bash
./install.sh list
```

## ➕ 添加新 Skill

### 方法 1：使用 skill-creator（推荐）

```bash
# 在仓库目录下运行
/skill-creator my-new-skill
```

### 方法 2：手动添加

1. 在当前目录创建新的 skill 文件夹：
   ```bash
   mkdir my-skill
   touch my-skill/SKILL.md
   ```

2. 编写 skill 内容（参考现有 skill 的结构）

3. 同步到所有 AI 工具：
   ```bash
   ./install.sh
   ```

4. 提交到 Git：
   ```bash
   git add .
   git commit -m "feat: 添加 my-skill"
   git push
   ```

## 🔄 同步机制

### 添加新 skill 后的自动同步流程：

```
┌─────────────────────────────────────────┐
│  fengye-skills (本仓库)                 │
│  - 所有 skill 的真实文件存放于此         │
└─────────────┬───────────────────────────┘
              │  ./install.sh
              ▼
┌─────────────────────────────────────────┐
│  各 AI 工具的 skills 目录                │
│  - 软链接指向本仓库                      │
│  - 修改会反映到真实文件                  │
└─────────────────────────────────────────┘
```

### 软链接结构示例：

```
~/.claude/skills/
├── agent-browser -> ~/workspace/fengye-skills/agent-browser
├── autoresearch -> ~/workspace/fengye-skills/autoresearch
├── fengye-blog-style -> ~/workspace/fengye-skills/fengye-blog-style
└── ...

~/.trae/skills/
├── agent-browser -> ~/workspace/fengye-skills/agent-browser
└── ... (同样的软链接结构)
```

## 🛠️ 开发工作流

### 修改现有 skill

1. 直接在本仓库中编辑 skill 文件
2. 测试更改（因为软链接的存在，各 AI 工具会立即生效）
3. 提交更改：
   ```bash
   git add .
   git commit -m "update(xxx): 修改描述"
   git push
   ```

### 删除 skill

1. 从本仓库删除目录：
   ```bash
   rm -rf skill-name
   ```

2. 重新运行 install.sh 清理各工具中的软链接：
   ```bash
   ./install.sh
   ```

3. 提交更改：
   ```bash
   git add .
   git commit -m "remove(xxx): 删除 skill-name"
   git push
   ```

## 📋 目录结构

```
fengye-skills/
├── README.md              # 本文件
├── install.sh             # 软链接管理脚本
├── agent-browser/         # 浏览器自动化
├── autoresearch/          # Skill 自动优化
├── copywriting/           # 文案撰写
├── create-readme/         # README 生成
├── fengye-blog-style/     # 个人博客风格
├── find-skills/           # Skill 发现
├── frontend-design/       # 前端设计
├── macos-design-guidelines/ # macOS 设计规范
├── skill-creator/         # Skill 创建工具
├── typescript-expert/     # TypeScript 专家
├── ui-ux-pro-max/         # UI/UX 设计
├── web-design-guidelines/ # Web 设计规范
└── webapp-testing/        # Web 应用测试
```

## 🔗 相关链接

- Skills 生态: https://skills.sh
- Claude Code 文档: https://docs.claude.ai

---

**注意**：本仓库是个人 skills 的集中管理地，所有修改都会通过软链接实时反映到各 AI 工具中。请务必小心操作！
