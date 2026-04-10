# AGENTS.md — 本仓库的 Agent 工作规范

## 仓库用途

本仓库是所有 AI 工具 skills 的**唯一真实来源**。各 AI 工具的 skills 目录通过软链接指向此处。

## 强制规范（必须遵守）

### 1. 修改后必须安装

对任何 skill 做了增删改后，**必须**运行安装脚本将变更同步到所有 AI 工具：

```bash
./install.sh
```

### 2. 修改后必须推送

安装完成后，**必须**提交并推送到 GitHub：

```bash
git add -A
git commit -m "描述你的变更"
git push
```

### 3. 完整流程

任何变更的完整流程是：

```bash
# 1. 做出修改（编辑 skill、新增 skill、删除 skill 等）
# 2. 安装到所有 AI 工具
./install.sh
# 3. 提交并推送
git add -A && git commit -m "你的 commit message" && git push
```

**不要跳过任何步骤。**

## Skill 目录结构

每个 skill 是一个独立目录，至少包含 `SKILL.md`：

```
skill-name/
├── SKILL.md          # 必须，skill 主文件
├── scripts/          # 可选，脚本工具
├── references/       # 可选，参考资料
├── evals/            # 可选，评测用例
│   └── evals.json
└── templates/        # 可选，模板文件
```

## 不要提交的文件

- `*-workspace/` — 评测工作目录（运行时产物）
- `*-report.html` — 评测报告（运行时产物）
- `**/.query_id_cache.json` — API 缓存（运行时产物）
- `run_functional_eval.py` — 临时评测脚本
