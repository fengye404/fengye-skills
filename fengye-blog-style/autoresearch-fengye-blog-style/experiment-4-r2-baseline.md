# Experiment #4 — Round 2 Baseline (Expanded Evals: E1-E8)

## Purpose
Re-establish baseline with 3 new evals added: E6-真实场景开头, E7-无AI过渡句, E8-有第一人称工程叙事. Using the same 0.0.2 skill that scored 100% on E1-E5.

---

## Run 1 — 场景1: 续写博客（Spring Boot 3 迁移）

### Output:

Spring Boot 3 把 javax 命名空间全部迁到了 jakarta。这个改动的影响比看起来大——除了源代码里的 import 要全量替换，XML 配置、第三方库的 SPI 文件、甚至测试代码里的 mock 都会受影响。

`javax.servlet.http.HttpServletRequest` 变成了 `jakarta.servlet.http.HttpServletRequest`。如果项目用了 OpenAPI/Swagger 的 springfox 库，直接跑不起来，因为 springfox 没跟进 jakarta 迁移。替代方案是切到 springdoc-openapi v2。

批量替换建议用 OpenRewrite 的 `org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta` recipe，可以自动处理 import 语句和配置文件。手动替换容易遗漏测试代码里的 javax 引用。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — javax, jakarta, springfox, springdoc-openapi, OpenRewrite, SPI
- E5 无重复解释: **PASS**
- E6 真实场景开头: **FAIL** — 开头是抽象技术事实陈述（"Spring Boot 3 把 javax..."），无具体工程经历或个人场景
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **FAIL** — 全文无第一人称，纯客观描述
- **Score: 6/8**

---

## Run 2 — 场景2: 调研 autoresearch 写博客

### Output:

Autoresearch 的核心思路是把 Andrej Karpathy 的自主实验循环从 ML 训练迁移到 prompt 工程。

传统的 prompt 优化依赖人工迭代：写 prompt、看输出、凭感觉改、再看输出。这个过程效率低且不可复现。autoresearch 把它系统化——定义二元 eval 标准，自动跑多轮实验，用贪心策略只保留有效的改动。

关键约束是 eval 必须是二元的。分数评估（1-7 分制）在 LLM 做 judge 时方差太大，同一个输出可能在不同次评估中得到差 3 分的结果。二元判断的一致性显著更高。

eval 设计有个平衡问题：太宽泛（"输出是否有用？"）会让判断不稳定，太狭窄（"是否少于 200 字？"）会让优化方向偏。好的 eval 应该是具体、可机器判断、但不偏颇。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — binary eval, LLM judge, greedy strategy, prompt engineering
- E5 无重复解释: **PASS**
- E6 真实场景开头: **FAIL** — 以抽象概念定义开头（"Autoresearch 的核心思路是..."），不是真实经历
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **FAIL** — 无第一人称
- **Score: 6/8**

---

## Run 3 — 场景3: 对当前代码仓库（TermPilot）写博客

### Output:

TermPilot 是一个远程终端协作工具，让 AI agent 能通过浏览器操作远程服务器的终端。

架构分三层：前端（React + xterm.js）、中继服务（relay）、和 agent 进程。前端负责终端渲染和用户交互，relay 负责权限控制和消息转发，agent 负责理解用户意图并生成命令。

relay 层是整个系统的关键。agent 发出的每个命令都要经过 relay 的权限检查——读操作直接放行，写操作弹窗确认，高危操作（rm -rf、sudo）强制二次确认。权限策略以 JSON 配置文件定义，运维人员可以按需调整。

通信层面，relay 和 agent 之间用自定义 JSON-RPC 协议而非 HTTP REST。选择 JSON-RPC 的理由是双向通信——relay 需要主动推消息给 agent（比如用户取消了操作），WebSocket 上的 JSON-RPC 天然支持这个需求。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — React, xterm.js, relay, JSON-RPC, WebSocket, PTY
- E5 无重复解释: **PASS**
- E6 真实场景开头: **FAIL** — 以项目定义开头（"TermPilot 是一个..."），不是个人经历
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **FAIL** — 无第一人称
- **Score: 6/8**

---

## Run 4 — 场景1: 续写博客（Spring Boot 3 第二次）

### Output:

Boot 3 迁移过程中，测试相关的依赖变更最容易被忽视。

Spring Boot 3 移除了对 JUnit 4 的默认支持。`spring-boot-starter-test` 不再引入 JUnit 4 和 Vintage Engine。如果项目的测试还在用 `@RunWith(SpringRunner.class)` 而非 `@ExtendWith(SpringExtension.class)`，升级后所有测试直接跑不起来。

迁移方案分两步：第一步，把 `@RunWith` 全部替换为 `@ExtendWith`；第二步，如果有遗留的 JUnit 4 API 调用（比如 `Assert.assertEquals`），改成 JUnit 5 的 `Assertions.assertEquals`。OpenRewrite 同样提供了自动化 recipe：`org.openrewrite.java.testing.junit5.JUnit4to5Migration`。

一个值得注意的细节是 Mockito 版本。Boot 3 内置的 Mockito 升级到了 5.x，如果项目有 Mockito 的 inline mock 配置，需要检查兼容性。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — JUnit 4/5, Vintage Engine, @RunWith, @ExtendWith, Mockito 5.x, OpenRewrite
- E5 无重复解释: **PASS**
- E6 真实场景开头: **FAIL** — 抽象陈述开头
- E7 无AI过渡句: **FAIL** — "一个值得注意的细节是" 属于 AI 过渡句模式 "一个X是Y"
- E8 有第一人称工程叙事: **FAIL** — 无第一人称
- **Score: 5/8**

---

## Run 5 — 场景2: 调研 autoresearch 写博客（第二次）

### Output:

把 autoresearch 用在 prompt 优化上，最直接的好处是消除了"凭感觉改 prompt"的随机性。

传统做法是：看了几个输出觉得不好，改一句 prompt 的措辞，再看几个输出觉得好了，就提交。问题是你无法确认改动和输出质量之间的因果关系，也无法排除样本偶然性。

autoresearch 框架要求三件事：固定的测试输入集、二元 eval 标准、足够的运行次数。满足这三个条件后，每次改动的效果可以量化——分数涨了才保留，没涨就回退。

更重要的是，这个循环可以完全自主运行。agent 不需要人工干预——它自己生成输出、自己评估、自己决定改动方向。人类只需要在开始时定义好 eval 标准，结束时审阅最终的 skill 文件。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — binary eval, prompt, agent, greedy
- E5 无重复解释: **PASS**
- E6 真实场景开头: **FAIL** — "把 autoresearch 用在..." 是抽象方法论陈述
- E7 无AI过渡句: **FAIL** — "更重要的是" 是 AI 过渡句
- E8 有第一人称工程叙事: **FAIL** — 无第一人称
- **Score: 5/8**

---

## Experiment 4 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | Score |
|-----|----------|----|----|----|----|----|----|----|----|-------|
| 1   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | 6/8   |
| 2   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | 6/8   |
| 3   | 代码仓库写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | 6/8   |
| 4   | 续写博客v2 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | 5/8   |
| 5   | 调研写博客v2 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | 5/8   |

**Total score: 28/40 (70.0%)**

Per-eval breakdown:
- E1-开头无套话: 5/5
- E2-无反模式: 5/5
- E3-语气硬无模糊词: 5/5
- E4-具体工程名词: 5/5
- E5-无重复解释: 5/5
- E6-真实场景开头: 0/5 ← **主要失败点**
- E7-无AI过渡句: 3/5
- E8-有第一人称工程叙事: 0/5 ← **主要失败点**

**Analysis:** E1-E5 全部通过（Round 1 的优化成果保持住了）。新 eval 揭示了两个明显短板：
1. E6 (0/5)：skill 的结构建议写的是"先定义主题"，导致输出总以抽象概念开头。参考博客的做法是从真实场景/经历切入。
2. E8 (0/5)：skill 没有任何关于第一人称视角的指令，输出全部是纯客观叙述。
3. E7 (3/5)：AI 过渡句（"一个值得注意的是"、"更重要的是"）未被禁止列表覆盖。

**Mutation target for next experiment:** E6 + E8（同时修复，因为它们本质上指向同一个问题——skill 引导模型写"技术文档"而非"个人博客"）。
