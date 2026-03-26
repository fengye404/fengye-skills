# fengye-skills

存放个人 Copilot Agent Skills 的仓库。

每个 skill 按版本管理，目录结构如下：

## 目录结构

```
fengye-skills/
└── <skill-name>/
    ├── <skill-name>-0.0.1/
    │   ├── SKILL.md
    │   └── ...
    └── <skill-name>-0.0.2/
        ├── SKILL.md
        └── ...
```

每个版本号子目录是独立的完整 skill，包含 `SKILL.md` 及其依赖文件。

## Skill 版本记录

### fengye-blog-style

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.0.1 | 2026-03-27 | 初始版本 |
| 0.0.2 | 2026-03-27 | autoresearch 优化：强化反模式禁令（绝对禁止+示例）、要求第一人称视角、真实场景开头、禁止 AI 过渡句 |
