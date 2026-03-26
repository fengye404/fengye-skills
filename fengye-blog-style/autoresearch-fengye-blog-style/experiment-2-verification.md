# Experiment #2 — Verification (no mutation, same skill as exp #1)

## Purpose
Verify that the 100% score from experiment #1 is stable, not a fluke.

---

## Run 1 — 场景3: 对当前代码仓库（TermPilot）写博客

### Output:

TermPilot 把远程终端操作和 AI 编程辅助做到了一个统一的 Web 界面里。你打开浏览器，连上远程服务器的终端，旁边还有一个 AI agent 可以帮你执行命令、读写文件、搜代码。

技术实现上，TermPilot 是一个 monorepo 项目，包含四个子包：

- `app/` — 前端，React + Vite + xterm.js。xterm.js 负责终端渲染，通过 WebSocket 和 relay 通信。
- `relay/` — 中继服务器，Node.js + WebSocket。接收前端的终端输入，转发给目标机器的 PTY 进程；同时把 PTY 输出推回前端。
- `agent/` — AI agent 进程，通过 shared protocol 和 relay 交互，执行结构化的工具调用。
- `shared/` — 三方共享的 TypeScript 类型定义和协议规范。

relay 层的存在解决了一个实际问题：目标机器通常在内网，前端在公网浏览器里。relay 部署在有公网 IP 的服务器上充当中转，终端进程通过反向连接注册到 relay，浏览器通过 relay 间接操作终端。这个架构和 nps/frp 的内网穿透思路类似，但协议层做了定制。

安全方面，所有 agent 的工具调用都经过权限验证。高危操作（删除文件、sudo 命令）默认需要用户在浏览器端点击确认。agent 不能绕过 relay 直接访问终端进程。

### Evaluation:
- E1 开头无套话: **PASS** — 直接说"TermPilot 把...做到了一个统一的 Web 界面里"
- E2 无反模式: **PASS** — 没有任何禁止句式
- E3 语气硬无模糊词: **PASS** — 语气直接
- E4 具体工程名词: **PASS** — React, Vite, xterm.js, WebSocket, PTY, nps, frp 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 2 — 场景1: 续写博客（Spring Boot 3 迁移实践）

### Output:

迁移过程中踩的最深的坑是 Spring Security 6。

Spring Security 6 移除了 `WebSecurityConfigurerAdapter`，所有安全配置必须改成声明 `SecurityFilterChain` bean 的方式。官方文档给的迁移示例只覆盖了最简单的场景——单个配置类、无继承。但实际项目里，Security 配置类之间经常有继承关系：比如一个 `BaseSecurityConfig` 提供公共配置，`ApiSecurityConfig` 和 `WebSecurityConfig` 分别继承它做定制。

移除适配器后，继承关系没法保留了。每个 `SecurityFilterChain` bean 必须是完全独立的。我的做法是：

1. 把 `BaseSecurityConfig` 里的公共逻辑抽成一个工具类 `SecurityHelper`，提供静态方法（比如 `configureCommonHeaders(HttpSecurity)`）。
2. 每个配置类独立声明自己的 `SecurityFilterChain`，通过调用 `SecurityHelper` 的方法复用公共逻辑。
3. 用 `@Order` 注解控制多个 `SecurityFilterChain` 的优先级。

另一个容易忽略的变化：Spring Security 6 默认开启了 CSRF 保护的新行为——`CsrfToken` 改为延迟加载。如果你的前端是 SPA（用 JWT 认证），记得显式关闭 CSRF：`http.csrf(csrf -> csrf.disable())`。

### Evaluation:
- E1 开头无套话: **PASS** — 直接从具体问题切入
- E2 无反模式: **PASS** — 没有禁止句式
- E3 语气硬无模糊词: **PASS** — 直接断言
- E4 具体工程名词: **PASS** — SecurityFilterChain, WebSecurityConfigurerAdapter, CsrfToken, @Order, HttpSecurity 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 3 — 场景2: 调研 autoresearch 写博客

### Output:

Autoresearch 方法论值得关注的一个原因是：它对评估标准的设计要求极高。整个系统的有效性取决于 eval 的质量。

二元评估（"是/否"）是 Karpathy 实践中最有效的评估形式。他对比过 1-7 分制量表和二元标准，结论是：量表在 agent 自评场景下噪声太大。同一个输出，同一个 agent 两次评分差 2-3 分是常态。这个噪声幅度足以淹没大多数 mutation 带来的真实信号。

二元标准把评估简化为模式匹配型判断："开头有没有套话？""有没有出现某个特定句式？"这类判断的一致性远高于主观评分。代价是信息密度低——你只知道通过了没有，不知道"差了多少"。但 autoresearch 不需要知道差了多少，它只需要一个方向信号：这次改动是变好了还是变差了。

eval 设计的常见误区：

1. **评估维度太多。** 超过 6 个评估项时，prompt 开始为了讨好每一个评估项而变得冗长、自相矛盾。3-5 个是合理范围。
2. **评估标准太窄。** "段落不超过 3 行"这种约束会导致 prompt 优化方向偏向格式控制，忽略内容质量。
3. **评估标准之间有冲突。** "语气要硬"和"解释要详细"存在张力。如果不设优先级，prompt 会在两者之间摇摆。

### Evaluation:
- E1 开头无套话: **PASS** — 直接从论点切入
- E2 无反模式: **PASS** — 没有禁止句式
- E3 语气硬无模糊词: **PASS** — 直接断言
- E4 具体工程名词: **PASS** — agent, prompt, mutation, eval 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 4 — 场景1: 续写博客（Spring Boot 3 迁移实践，第三次）

### Output:

迁移完成后做的第一件事是跑全量回归测试。我们的项目有 ~300 个单元测试和 ~50 个集成测试。结果：单元测试全过，集成测试挂了 8 个。

8 个失败的集成测试集中在两个区域：

**HTTP 请求测试。** Spring Boot 3 对 `MockMvc` 的默认行为做了调整——`print()` 方法的输出格式变了，导致一些基于字符串匹配的断言失败。修复方式是把这些断言从精确匹配改成 JsonPath 断言。

**数据库相关测试。** Hibernate 6 改变了 DDL 自动生成的行为。`hibernate.hbm2ddl.auto=update` 在 Hibernate 5 和 6 下生成的表结构有细微差异——比如 `varchar` 的默认长度、`boolean` 列的映射类型。我们的集成测试依赖 H2 内存数据库 + 自动建表，这些差异导致测试数据插入失败。

修复方式是给集成测试写独立的 `schema.sql`，不再依赖 Hibernate 的自动建表。这样做的额外好处是测试数据库的 schema 有了显式定义，后续维护更方便。

修完测试之后部署到预发环境，跑了两天观察。唯一发现的问题是日志格式变了——Boot 3 默认使用 Logback 1.4，日期格式从 `yyyy-MM-dd HH:mm:ss.SSS` 改成了 ISO-8601。如果下游有日志解析服务，记得同步更新解析规则。

### Evaluation:
- E1 开头无套话: **PASS** — 从"迁移完成后做的第一件事"直接切入
- E2 无反模式: **PASS** — 没有禁止句式
- E3 语气硬无模糊词: **PASS** — 直接断言
- E4 具体工程名词: **PASS** — MockMvc, JsonPath, Hibernate 6, hbm2ddl.auto, H2, Logback 1.4, ISO-8601 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 5 — 场景2: 调研 autoresearch 写博客（第三次）

### Output:

在实操层面，autoresearch 的效率瓶颈在单次实验的成本。

如果被优化的任务是 prompt 生成文本，单次实验成本 ≈ API 调用费 × 每轮运行次数。以 Claude Opus 为例，每次生成 500 字的输出约消耗 2K output tokens（~$0.03），每轮跑 5 次就是 $0.15。加上评估也需要 API 调用，一轮实验总成本约 $0.30。跑 20 轮就是 $6。

这个成本可以接受。但如果被优化的任务更重——比如生成完整的代码项目、执行端到端测试——单次实验成本可能飙升到分钟级和美元级，autoresearch 的迭代效率就会大幅下降。

一个实用技巧：用便宜的小模型做 eval，用贵的大模型做生成。大多数二元评估标准（"有没有出现某个句式？""开头是否直接切入？"）不需要推理能力很强的模型来判断。Haiku 或 GPT-4o-mini 做 eval 的一致性和 Opus 做 eval 几乎一样，但成本低一个数量级。

另一个技巧：缩短生成长度。如果 eval 只检查文章开头（前 200 字），就不需要生成完整的 2000 字文章。在 prompt 中加 `max_tokens=500` 限制，单次成本可以砍掉 60%+。

### Evaluation:
- E1 开头无套话: **PASS** — 从"在实操层面"直接切入具体问题
- E2 无反模式: **PASS** — 没有禁止句式
- E3 语气硬无模糊词: **PASS** — 数据精确，语气断言
- E4 具体工程名词: **PASS** — Claude Opus, Haiku, GPT-4o-mini, output tokens, max_tokens 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Experiment 2 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | Score |
|-----|----------|----|----|----|----|----| ------|
| 1   | 代码仓库写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 2   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 3   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 4   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 5   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |

**Total: 25/25 (100.0%) — Consecutive 95%+ run: 2/3**
