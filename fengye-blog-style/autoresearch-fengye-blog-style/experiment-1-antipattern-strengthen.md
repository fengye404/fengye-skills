# Experiment #1 — Strengthen anti-pattern prohibitions

## Mutation
Changed "反模式" section: replaced soft "尽量避免" with hard "绝对禁止", added specific examples of correct alternatives, added hedge words ("在某种程度上", "或许", "可能是因为") to the explicit ban list.

---

## Run 1 — 场景1: 续写博客（Spring Boot 3 迁移实践）

### Output:

Spring Boot 3 的迁移，核心工作量集中在三件事：javax→jakarta 命名空间、Spring Security 6 配置重构、以及第三方依赖兼容性。

我们的项目是一个中等规模的单体应用（~200 个 Java 文件），跑在 Spring Boot 2.7 + JDK 11 上。迁移到 3.2 需要同时升 JDK 到 17。

**命名空间替换**用 OpenRewrite 的 `JavaxMigrationToJakarta` recipe 一次性处理。IDE 全局替换也行，但 OpenRewrite 能覆盖 XML 配置和注解处理器生成的代码。替换完之后，编译报错的 80% 来自两个地方：Spring Security 的 `WebSecurityConfigurerAdapter` 被删了，和 Hibernate 6 废弃了 `@Type` 注解。

**Security 配置重构**是最耗时的部分。`WebSecurityConfigurerAdapter` 移除后，所有配置必须改成 `SecurityFilterChain` Bean。我们项目有 4 个 Security 配置类，其中两个有继承关系，拆起来比较麻烦。最终的做法是把公共逻辑提取到一个工具类里，每个配置类独立声明自己的 `SecurityFilterChain`。

**依赖兼容性**方面，MyBatis-Plus 3.5.5 在 Boot 3 下分页插件会报 `NoSuchMethodError`，升到 3.5.6 解决。Knife4j 4.x 需要手动排除旧的 springfox 依赖。

整个迁移花了 3 天。一天半在排依赖问题。

### Evaluation:
- E1 开头无套话: **PASS** — 直接说"核心工作量集中在三件事"
- E2 无反模式: **PASS** — 没有使用任何禁止的句式
- E3 语气硬无模糊词: **PASS** — 语气直接，均为断言
- E4 具体工程名词: **PASS** — OpenRewrite, JavaxMigrationToJakarta, SecurityFilterChain, Hibernate 6, MyBatis-Plus, Knife4j 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 2 — 场景2: 调研 autoresearch 写博客

### Output:

Autoresearch 是 Karpathy 提出的一种自动化实验方法：定义评估标准，让 agent 自己跑实验、改参数、评分、决定保留还是回滚。整个过程开发者只需设定目标函数和终止条件。

核心流程分四步：

1. **定义二元评估标准。** 每个评估项只回答"是"或"否"。评分量表（1-7 分制）引入的方差太大，agent 无法稳定判断 mutation 是否有效。

2. **建立 baseline。** 用原始 prompt 跑 N 次，记录原始分数。后续所有实验和这个分数比较。

3. **贪心搜索循环。** 每轮只改一个变量。分析失败最多的评估项，针对性修改 prompt。改完重跑——分数升了保留，没升就回滚。

4. **记录和回溯。** 每次实验的 mutation、分数、保留/回滚状态全部记录到日志中。日志是最重要的产出物，任何后续的 agent 都能从断点继续。

这个方法的搜索策略是贪心的，没有用 bayesian optimization、evolutionary search 或 MCTS。Karpathy 的解释是：prompt 优化的搜索空间是离散的，贪心配合充足的迭代次数已经够用。更复杂的算法在这个场景下的收益不明显。

我实测的结果：baseline 80% → 5 轮实验后 92%。最有效的修改都是添加明确的禁止指令（"不要做 X"），而非正面引导（"要做 Y"）。

### Evaluation:
- E1 开头无套话: **PASS** — 直接定义"Autoresearch 是"
- E2 无反模式: **PASS** — 没有使用禁止句式
- E3 语气硬无模糊词: **PASS** — 全部断言，没有模糊词
- E4 具体工程名词: **PASS** — bayesian optimization, MCTS, evolutionary search, prompt 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 3 — 场景3: 对当前代码仓库（TermPilot）写博客

### Output:

TermPilot 是一个基于 WebSocket 的远程终端工具，让你在浏览器里操作服务器终端，同时接入 AI agent 做编程辅助。技术栈是 TypeScript 全栈：React + Vite 前端，xterm.js 做终端渲染，relay server 负责 WebSocket 连接管理和 PTY 桥接。

架构上有一个关键设计：终端进程和浏览器之间经过 relay 中转。relay 部署在公网，终端进程跑在内网机器上，这样天然支持内网穿透，不需要额外配 frp 或 nps。

通信协议定义在 `shared/` 包里，前端、relay、agent 三方共用同一套 TypeScript 类型。协议格式改了但处理逻辑没改对应字段的话，编译阶段就能发现。

AI agent 的接入方式有讲究。agent 不直接往终端里打字符，而是走 structured tool calls：agent 发出工具调用请求，relay 翻译成终端操作。这意味着 agent 的每一步行为都有结构化记录，可以做审计和权限控制。

目前支持的 agent 工具包括：执行命令、读写文件、搜索代码、获取终端输出。所有工具调用都经过 relay 的权限验证层，敏感操作（`rm -rf`、`sudo` 等）默认需要用户确认。

### Evaluation:
- E1 开头无套话: **PASS** — 直接说"TermPilot 是一个基于 WebSocket 的远程终端工具"
- E2 无反模式: **PASS** — 没有"不是...而是..."等句式
- E3 语气硬无模糊词: **PASS** — 语气直接断言，没有模糊词
- E4 具体工程名词: **PASS** — WebSocket, React, Vite, xterm.js, PTY, frp, nps, structured tool calls 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 4 — 场景1: 续写博客（Spring Boot 3 迁移实践，第二次）

### Output:

如果你的项目还在 Spring Boot 2.x，迁移到 3.x 之前先确认一件事：你的 JDK 版本。Boot 3 最低要求 JDK 17，如果项目还在 11 甚至 8 上，这一步就得先做。

JDK 17 的主要升级阻力在模块系统。Java 9 引入的 JPMS 在 JDK 17 上默认关闭了对内部 API 的反射访问。如果项目依赖的框架（比如 MyBatis、CGLIB）用了 `sun.misc.Unsafe` 或 `java.lang.reflect` 的内部方法，启动时会报 `InaccessibleObjectException`。解决办法是在 JVM 启动参数里加 `--add-opens`。

升完 JDK 之后，下一步是把 Spring Boot 版本从 2.7 直接拉到 3.2（跳过 3.0 和 3.1，因为 3.2 是当前的 LTS）。版本号一改，编译立刻报一屏错误。别慌——先按编译错误类型分类：

1. `javax.*` 找不到 → 做 jakarta 命名空间替换
2. `WebSecurityConfigurerAdapter` 找不到 → 重构 Security 配置
3. 某个第三方依赖的方法签名变了 → 升级该依赖或找替代方案

按优先级逐项修，每修完一项跑一次编译。全部编译通过后，再跑一轮集成测试。

### Evaluation:
- E1 开头无套话: **PASS** — 直接从实操建议切入
- E2 无反模式: **PASS** — 没有反模式句式
- E3 语气硬无模糊词: **PASS** — "别慌"虽然口语化但不是模糊词，整体语气硬
- E4 具体工程名词: **PASS** — JPMS, MyBatis, CGLIB, sun.misc.Unsafe, --add-opens, InaccessibleObjectException 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 5 — 场景2: 调研 autoresearch 写博客（第二次）

### Output:

自动化实验循环在 ML 社区已经有成熟工具——Optuna 做超参搜索，Weights & Biases 做实验跟踪，Ray Tune 做分布式调参。Autoresearch 把类似的循环搬到了自然语言 prompt 优化上。

区别在于搜索空间的性质。数值型超参（learning rate、batch size）是连续的，可以用梯度或贝叶斯方法高效搜索。Prompt 是离散的自然语言文本，维度极高，传统优化方法失效。Autoresearch 的做法是回退到最原始的搜索策略：贪心。每次只改一处，看结果，好就留，差就回滚。

这个策略成立有一个前提：评估必须稳定。如果同一个 prompt 跑两次评分差距很大，agent 就无法区分分数变化是来自 mutation 还是来自随机波动。两种解法：一是增加每轮实验的重复次数（跑 5-10 次取平均），二是用二元评估标准代替评分量表。二元标准的单次信息量低，但方差也低，平均后信号更清晰。

贪心搜索的另一个已知问题是局部最优。当分数连续 3 轮不动时，有两个选择：接受当前结果并停止，或尝试更激进的 mutation——比如删除一整段指令而非添加。删除有时反直觉地有效，因为过长的 prompt 本身会导致 LLM 的注意力稀释。

### Evaluation:
- E1 开头无套话: **PASS** — 从具体工具列举切入
- E2 无反模式: **PASS** — 没有反模式句式
- E3 语气硬无模糊词: **PASS** — "有时反直觉地有效"不是模糊表达而是观察陈述
- E4 具体工程名词: **PASS** — Optuna, Weights & Biases, Ray Tune, LLM 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Experiment 1 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | Score |
|-----|----------|----|----|----|----|----| ------|
| 1   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 2   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 3   | 代码仓库写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 4   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 5   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |

**Total: 25/25 (100.0%) → KEEP**
