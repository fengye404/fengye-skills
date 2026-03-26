# Experiment #3 — Third consecutive verification

## Purpose
Third consecutive 95%+ check. If this also hits 95%+, autoresearch stops (diminishing returns).

---

## Run 1 — 场景2: 调研 autoresearch 写博客

### Output:

把 autoresearch 应用到非 ML 场景有一个前提条件：你得能定义出稳定的二元评估标准。

ML 领域这个问题天然解决——loss function 和 metrics 就是评估标准。但在文本生成、代码生成这类任务里，"好"的定义是模糊的。autoresearch 的做法是把模糊的质量标准拆解为多个可机器判断的二元检查。

举个例子：评估一篇技术博客的"写作质量"太宽泛，agent 无法给出稳定的判断。但如果拆成：

- 开头有没有使用套话？（是/否）
- 有没有出现"不是...而是..."的句式？（是/否）
- 是否包含至少 3 个具体工程名词？（是/否）

每一项都能得到一致的评判结果。5 个这样的检查项组合起来，就构成了一个对"写作质量"的近似度量。

这种拆解方式的局限在于覆盖面。5 个检查项无法涵盖所有的质量维度。如果某个维度没被 eval 覆盖到，agent 的优化方向会偏——分数提升了，但人类读起来觉得"哪里不对"。这就是 Goodhart's Law 在 prompt 优化中的体现。

实际操作中的建议：先用 3-5 个 eval 跑一轮，看完结果后再决定是否追加新的 eval 维度。追加时同样遵循贪心原则——一次只加一个。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS** — 引用 "不是...而是..." 是作为例子讨论，不是在正文中使用
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS**
- E5 无重复解释: **PASS**
- **Score: 5/5**

---

## Run 2 — 场景3: 对当前代码仓库（TermPilot）写博客

### Output:

TermPilot 的 agent 系统设计了一个分层的权限模型。

最底层是工具层（tool layer）。agent 能调用的工具有明确的范围：`execute_command`、`read_file`、`write_file`、`search_code`、`get_terminal_output`。每个工具有预定义的参数 schema，agent 传入结构化参数，relay 校验后执行。

中间层是权限层（permission layer）。relay 维护一个权限配置，定义哪些操作需要用户确认。默认策略是：读操作（`read_file`、`search_code`）自动放行，写操作（`write_file`）需确认，高危操作（`rm`、`sudo`、`chmod`）强制确认。这个配置用户可以自定义。

最上层是审计层（audit layer）。所有 agent 的工具调用——包括参数、返回值、执行时间——都被记录到 relay 的日志中。这个日志是纯结构化的 JSON，后续做回放或分析很方便。

这个三层设计的好处是解耦。如果你只想改权限策略（比如把 `write_file` 也改成自动放行），只需要修改 relay 的配置文件，不需要动 agent 或前端的代码。

一个实现细节：agent 进程和 relay 之间用的是自定义的 JSON-RPC 协议。选择自定义协议而非 HTTP REST 的原因是延迟——WebSocket 上的 JSON-RPC 是双向的，relay 可以主动推消息给 agent（比如用户取消了某个操作），REST 做不到这一点。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — JSON-RPC, WebSocket, execute_command, permission layer 等
- E5 无重复解释: **PASS**
- **Score: 5/5**

---

## Run 3 — 场景1: 续写博客（Spring Boot 3 迁移）

### Output:

迁移里一个容易被忽视的点：Spring Boot 3 改变了默认的 URL 匹配策略。

Boot 2.x 默认使用 `AntPathMatcher`，Boot 3 切换到了 `PathPatternParser`。两者的行为差异在大多数场景下无感知，但有一个边缘情况：URL 末尾的 `/`。

`AntPathMatcher` 默认做 trailing slash 匹配——`/api/users` 和 `/api/users/` 指向同一个 controller 方法。`PathPatternParser` 默认不做。如果你的前端或 API 客户端发送的请求带 trailing slash，升级后会收到 404。

修复有两种方式：

1. 在 `WebMvcConfigurer` 中显式配置 `setUseTrailingSlashMatch(true)`——但这个方法在 Boot 3.x 中已标记为 `@Deprecated`，后续版本会移除。
2. 统一所有客户端的请求路径，去掉 trailing slash。如果是内部 API 还好改，如果是对外的公开接口，这个变更需要考虑兼容性。

我们选了第二种。在 Nginx 反向代理层加了一条 rewrite 规则，自动去掉请求路径末尾的 `/`。这样不需要改客户端代码，也不依赖 Spring 的废弃 API。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — AntPathMatcher, PathPatternParser, WebMvcConfigurer, @Deprecated, Nginx, rewrite 等
- E5 无重复解释: **PASS**
- **Score: 5/5**

---

## Run 4 — 场景3: 对当前代码仓库（TermPilot）写博客（第二次）

### Output:

TermPilot 的前端终端渲染基于 xterm.js，这个选择基本是唯一解——Web 端做终端模拟，xterm.js 是事实标准，VS Code 的内置终端也用它。

前端和 relay 之间的通信协议分两类消息：

**终端数据流。** 用户键盘输入 → 前端通过 WebSocket 发送到 relay → relay 写入目标机器的 PTY stdin → PTY 输出写入 stdout → relay 推送到前端 → xterm.js 渲染。整条链路延迟目标在 50ms 以内。

**控制消息。** 终端 resize、会话创建/销毁、心跳检测。这类消息走同一条 WebSocket 连接，但用 `type` 字段区分。协议定义放在 `shared/src/protocol.ts` 里。

xterm.js 的一个坑：默认的键盘事件处理和浏览器的快捷键冲突。Ctrl+C 在终端里是发送 SIGINT，但浏览器默认把它当成"复制"。解决办法是在 xterm.js 的 `attachCustomKeyEventHandler` 里拦截冲突快捷键，根据终端是否有选中文本决定行为——有选中文本时走浏览器复制，无选中文本时发送 SIGINT 到终端。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — xterm.js, PTY, stdin, stdout, SIGINT, attachCustomKeyEventHandler, protocol.ts 等
- E5 无重复解释: **PASS**
- **Score: 5/5**

---

## Run 5 — 场景1: 续写博客（第四次变体）

### Output:

Spring Boot 3 迁移还有一个经常被遗忘的部分：Actuator endpoints 的路径变了。

Boot 2.x 的 Actuator 默认暴露在 `/actuator/*` 下，这一点 Boot 3 没变。但 `management.endpoints.web.base-path` 的默认行为有调整——如果你之前自定义了 Actuator 的 base path（比如改成 `/manage`），升级后需要检查是否仍然生效。

更重要的是 `info` endpoint 的变化。Boot 3 默认不再暴露 `info` endpoint 的 git 信息和 build 信息。如果你的运维监控依赖 `/actuator/info` 获取版本号和 commit id，升级后会发现返回的 JSON 变成了空对象。修复方法是在 `application.yml` 里显式开启：

```yaml
management:
  info:
    git:
      mode: full
    build:
      enabled: true
```

另外，Prometheus metrics endpoint 的依赖从 `micrometer-registry-prometheus` 变成了 `micrometer-registry-prometheus-simpleclient` 或 `micrometer-registry-prometheus`（取决于你用的 Prometheus 客户端版本）。如果升级后 `/actuator/prometheus` 返回 404，先检查 Maven/Gradle 依赖是否正确。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — Actuator, management.endpoints.web.base-path, micrometer-registry-prometheus, application.yml 等
- E5 无重复解释: **PASS**
- **Score: 5/5**

---

## Experiment 3 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | Score |
|-----|----------|----|----|----|----|----| ------|
| 1   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 2   | 代码仓库写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 3   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 4   | 代码仓库写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 5   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |

**Total: 25/25 (100.0%) — Consecutive 95%+ runs: 3/3 → STOP CONDITION MET**
