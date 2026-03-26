# Experiment #6 — Verification run (2/3 consecutive 95%+)

## Purpose
Verify that experiment 5's 100% score is stable, not a fluke. Same skill, different output variations.

---

## Run 1 — 场景3: 对当前代码仓库（TermPilot）写博客（relay 安全设计）

### Output:

做 TermPilot 的时候，安全模型是我纠结最久的部分。

核心矛盾很简单：agent 要操作终端，必须有执行命令的能力。但你不可能给一个 AI 进程不受限的 shell 权限——一条 `rm -rf /` 就完了。

我最后的方案是在 relay 层做权限拦截。所有命令都经过 relay 的 permission engine，按风险等级分三档：读操作（cat、ls、grep）自动放行，写操作（写文件、pip install）弹窗确认，高危操作（sudo、rm -rf、chmod 777）强制二次确认且记录审计日志。

权限配置是一个 JSON 文件，格式类似：

```json
{
  "auto_approve": ["read_file", "search_code"],
  "require_confirm": ["write_file", "execute_command"],
  "require_double_confirm": ["sudo", "rm -rf"]
}
```

运维团队可以按环境调整。生产环境可以把 `execute_command` 也升到 double_confirm。

实现上有个细节：权限检查必须在 relay 侧做，不能信任 agent 侧的自我约束。agent 进程可能被 prompt injection 操纵，所以安全边界必须在 relay——agent 只能通过 relay 暴露的 RPC 接口操作，没有绕过的路径。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — permission engine, relay, JSON-RPC, prompt injection, audit log
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "做 TermPilot 的时候，安全模型是我纠结最久的部分"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我纠结最久"、"我最后的方案"
- **Score: 8/8**

---

## Run 2 — 场景1: 续写博客（Spring Boot 3 — Actuator 迁移）

### Output:

升级 Boot 3 之后运维那边先发现了问题——监控面板上的版本号和 commit id 突然变成空的了。

查下来是 Actuator 的 `/actuator/info` endpoint 行为变了。Boot 3 默认不再暴露 git 信息和 build 信息。之前不需要配置是因为 Boot 2 默认开启，现在得在 `application.yml` 里显式声明：

```yaml
management:
  info:
    git:
      mode: full
    build:
      enabled: true
```

加完之后还有一个问题。我们用 Prometheus 采集 metrics，升级后 `/actuator/prometheus` 返回 404。原因是依赖名变了——`micrometer-registry-prometheus` 在 Boot 3 里要换成对应 Prometheus 客户端版本的 artifact。我们用的 Prometheus 2.x，对应的是 `micrometer-registry-prometheus-simpleclient`。Maven 里改一下 artifactId 就好了。

这种"默认值变了但没报错"的问题最难排查。代码能跑，测试能过，但生产环境的监控数据悄悄断了。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — Actuator, application.yml, micrometer-registry-prometheus, Prometheus 2.x, artifactId, Maven
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "升级 Boot 3 之后运维那边先发现了问题"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我们用 Prometheus"、"我们用的 Prometheus 2.x"
- **Score: 8/8**

---

## Run 3 — 场景2: 调研 autoresearch 写博客（eval 设计）

### Output:

上一轮 autoresearch 跑出 100% 的时候我没太高兴，因为直觉告诉我 eval 太简单了。

后来回头看生成的输出，果然有问题：5 个 eval 全过了，但文章读起来像技术文档，不像博客。没有第一人称视角，开头全是"X 是一种..."的概念定义。这些问题不在我的 eval 覆盖范围内。

这就是 Goodhart's Law 的典型表现：指标优化到头了，但真正想要的东西没拿到。解法是加更难的 eval。

我后来追加了三个：开头是否从真实场景切入（而非抽象定义）、有没有 AI 常见过渡句（"值得注意的是"这类）、文章里有没有第一人称工程叙事。加完之后分数一下从 100% 掉到 70%，说明新的 eval 确实抓到了之前漏检的问题。

eval 设计的教训：第一版 eval 不要追求完美覆盖，先跑一轮看输出，用人类直觉发现 eval 没抓到的问题，然后追加。这比一开始就写 10 个 eval 更有效——因为你只有看到真实输出之后才知道"差"在哪。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — Goodhart's Law, eval, binary eval, autoresearch
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "上一轮 autoresearch 跑出 100% 的时候"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我没太高兴"、"我后来追加了三个"
- **Score: 8/8**

---

## Run 4 — 场景3: 对当前代码仓库（TermPilot）写博客（前端终端渲染）

### Output:

TermPilot 的前端终端渲染我踩了不少坑，主要跟 xterm.js 和浏览器快捷键冲突有关。

xterm.js 是 Web 端做终端模拟的事实标准，VS Code 的内置终端也用它。集成本身不复杂，但有一个问题：Ctrl+C 在终端里是发 SIGINT，在浏览器里是"复制"。两个功能抢同一个快捷键。

我的处理方式是在 xterm.js 的 `attachCustomKeyEventHandler` 里拦截。逻辑是：如果终端里有选中文本，Ctrl+C 走浏览器的复制；如果没有选中文本，Ctrl+C 发送 `\x03`（SIGINT）到终端。Ctrl+V 类似——终端没有"粘贴"的概念，需要把剪贴板内容直接写入 PTY 的 stdin。

数据流是这样的：用户键盘输入 → 前端发 WebSocket → relay 写入 PTY stdin → PTY stdout 输出 → relay 推回前端 → xterm.js 渲染。整条链路的延迟目标是 50ms 以内，超过这个阈值用户会明显感觉到输入延迟。

终端 resize 也需要处理。用户拖拽浏览器窗口时，前端要计算新的行列数（基于字体大小和容器尺寸），然后发一条 resize 控制消息给 relay，relay 再调 PTY 的 `pty.resize(cols, rows)`。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — xterm.js, attachCustomKeyEventHandler, SIGINT, \x03, PTY, stdin, stdout, WebSocket, pty.resize
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 的前端终端渲染我踩了不少坑"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我踩了不少坑"、"我的处理方式是"
- **Score: 8/8**

---

## Run 5 — 场景1: 续写博客（Spring Boot 3 — URL 匹配策略）

### Output:

升级 Boot 3 后有一批接口突然返回 404，排查了半天才发现是 URL 匹配策略变了。

Boot 2.x 默认用 `AntPathMatcher`，Boot 3 换成了 `PathPatternParser`。两者在大多数情况下行为一致，但有个边缘情况：URL 末尾的 `/`。`AntPathMatcher` 默认做 trailing slash 匹配，`/api/users` 和 `/api/users/` 指向同一个 handler。`PathPatternParser` 默认不做。

我们的 API 客户端有些请求带 trailing slash，有些不带，之前从来没出过问题。升级后带 slash 的请求全 404 了。

修复有两个方向。一是在 `WebMvcConfigurer` 里设 `setUseTrailingSlashMatch(true)`，但这个方法 Boot 3.x 已标记 `@Deprecated`，迟早要移除。二是在 Nginx 反向代理做 rewrite，自动去掉 trailing slash。我们选了第二种——在 Nginx 加一条 rewrite 规则，不改客户端代码也不依赖废弃 API。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — AntPathMatcher, PathPatternParser, WebMvcConfigurer, @Deprecated, Nginx, trailing slash, handler
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "升级 Boot 3 后有一批接口突然返回 404"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "排查了半天"、"我们的 API 客户端"、"我们选了第二种"
- **Score: 8/8**

---

## Experiment 6 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | Score |
|-----|----------|----|----|----|----|----|----|----|----|-------|
| 1   | TermPilot安全 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 2   | Boot3 Actuator | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 3   | autoresearch eval | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 4   | TermPilot前端 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 5   | Boot3 URL匹配 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |

**Total score: 40/40 (100.0%)**

Consecutive 95%+ runs: **2/3**
