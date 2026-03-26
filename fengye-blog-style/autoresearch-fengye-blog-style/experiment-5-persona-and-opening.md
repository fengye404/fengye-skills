# Experiment #5 — Real-scenario openings + first-person voice + AI transition ban

## Mutation
1. Added new "视角与语气" section requiring first-person engineering narratives
2. Changed "引言" from "先定义主题" to "从真实场景切入" with explicit examples and prohibition on abstract concept openings
3. Added AI transition phrases to ban list: "值得注意的是", "需要指出的是", "更重要的是", "一个关键的X是", etc.

---

## Run 1 — 场景1: 续写博客（Spring Boot 3 迁移）

### Output:

最近在把公司一个老项目从 Spring Boot 2.7 升到 3.2，javax 到 jakarta 的命名空间迁移比预想的麻烦。

源代码里的 import 替换用 IDE 的全局替换就能搞定，但坑在第三方库。我们用了 springfox 做 API 文档，这个库到现在还没跟进 jakarta 命名空间，启动直接报 ClassNotFoundException。最后换成了 springdoc-openapi v2。

另一个没预料到的问题是 SPI 文件。`META-INF/services/` 下面的接口名也要从 javax 改成 jakarta，这个 IDE 的全局替换不会帮你处理。我用了 OpenRewrite 的 `JavaxMigrationToJakarta` recipe 做了一遍自动扫描，确实抓出来几个漏网的。

测试代码是重灾区。我们有些集成测试直接引用了 `javax.servlet.http.HttpServletRequest`，改完主代码忘了改测试，CI 跑到一半才发现。

### Evaluation:
- E1 开头无套话: **PASS** — 直接从真实项目经历切入
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — springfox, springdoc-openapi, JavaxMigrationToJakarta, SPI, META-INF/services, ClassNotFoundException
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "最近在把公司一个老项目从 Spring Boot 2.7 升到 3.2"，具体的工程经历
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我们用了"、"我用了 OpenRewrite"、"我们有些集成测试"
- **Score: 8/8**

---

## Run 2 — 场景2: 调研 autoresearch 写博客

### Output:

上周把我的博客写作 skill 拿去跑 autoresearch，结果挺有意思。

背景是我有一个 Claude Code 的 skill 文件，控制 AI 帮我写博客时的文风。但写出来的东西总有 30% 的概率带 AI 味——"不是...而是..."、"换句话说"这些句式会冒出来。手动改 skill 试了几次，没办法确认到底是改了管用还是碰巧。

autoresearch 的做法是把 prompt 优化系统化：定义几个二元 eval 标准（比如"开头有没有套话"、"有没有用禁止句式"），然后自动跑几十次，统计通过率。每次只改 skill 的一个地方，分数涨了就保留，没涨就回退。

我跑了一轮，baseline 是 80%，主要挂在"反模式"和"模糊词"两个 eval 上。改了一版——把"尽量避免"改成"绝对禁止"并加了具体的 ❌→✅ 示例——分数直接拉到 100%。后面连续验证了两轮，分数稳定。

一个限制：当前的 eval 是我自己定义的，模型自己评自己，存在 Goodhart's Law 的风险。分数到顶了不代表输出真的完美，可能只是 eval 不够难。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — binary eval, Goodhart's Law, baseline, skill, Claude Code
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "上周把我的博客写作 skill 拿去跑 autoresearch"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我有一个"、"手动改 skill 试了几次"、"我跑了一轮"
- **Score: 8/8**

---

## Run 3 — 场景3: 对当前代码仓库（TermPilot）写博客

### Output:

TermPilot 是我最近在做的一个项目，让 AI agent 通过浏览器远程操作服务器终端。

起因是我经常需要在服务器上调试，但 SSH 加 tmux 的工作流没法让 AI agent 参与进来。agent 没有终端访问权限，你只能手动复制粘贴它给的命令。TermPilot 想解决的就是这个问题——给 agent 一个受控的终端接口。

架构上分三层。前端基于 React + xterm.js 做终端渲染，relay 层负责 WebSocket 消息转发和权限控制，agent 进程通过自定义 JSON-RPC 协议和 relay 通信。

我在权限设计上花了不少时间。agent 可以读文件、搜索代码，这些操作自动放行。但写文件、执行命令这类操作必须弹窗让用户确认。高危命令（rm -rf、sudo）强制二次确认。权限策略是 JSON 配置文件，可以按团队需求调整。

选 JSON-RPC 而非 REST 的原因是双向通信需求。relay 需要主动给 agent 推消息（比如用户取消了操作），WebSocket 上的 JSON-RPC 天然支持这个。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — React, xterm.js, WebSocket, JSON-RPC, SSH, tmux, relay
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 是我最近在做的一个项目"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我最近在做的"、"我经常需要"、"我在权限设计上花了不少时间"
- **Score: 8/8**

---

## Run 4 — 场景1: 续写博客（Spring Boot 3 第二变体 — 测试迁移）

### Output:

升级 Boot 3 那周，CI 挂的最多的是测试。

我们项目的测试有一部分还在用 JUnit 4 的 `@RunWith(SpringRunner.class)`。Boot 3 的 `spring-boot-starter-test` 不再带 JUnit 4 依赖和 Vintage Engine，所以这些测试直接编译不过。

修的时候分了两步。第一步把 `@RunWith(SpringRunner.class)` 全部替换成 `@ExtendWith(SpringExtension.class)`，这个用 IDE 的结构化搜索就能批量处理。第二步是 JUnit 4 的 assertion API——`Assert.assertEquals` 改成 `Assertions.assertEquals`，参数顺序没变，但 import 路径变了。

Mockito 也有坑。Boot 3 内置 Mockito 5.x，我们之前用的 3.x 的一些 API 在 5.x 里行为变了。比如 `Mockito.mockStatic()` 在 5.x 里对 mock scope 的处理更严格，之前偷懒没关 scope 的测试全挂了。

OpenRewrite 有个 `JUnit4to5Migration` recipe，但我跑完发现它处理不了所有情况——自定义的 TestRule 和 ExternalResource 需要手动改。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — JUnit 4/5, @RunWith, @ExtendWith, Mockito 5.x, mockStatic, Vintage Engine, TestRule, ExternalResource
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "升级 Boot 3 那周，CI 挂的最多的是测试"，真实经历
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我们项目"、"修的时候分了两步"、"我跑完发现"
- **Score: 8/8**

---

## Run 5 — 场景2: 调研 autoresearch 写博客（第二变体）

### Output:

我给自己的博客 skill 跑了一轮 autoresearch，想验证 Karpathy 说的"让 agent 自己优化自己"在 prompt 领域能不能跑通。

实验设计是这样的：定了 5 个二元 eval（开头有没有套话、有没有用禁止句式、语气够不够硬、有没有具体工程名词、有没有重复解释），每个实验跑 5 次，满分 25 分。

baseline 跑出来 20 分，80%。失败集中在两个 eval：反模式句式（"不是...而是..."）和模糊词（"在某种程度上"）。原来的 skill 写的是"尽量避免"，模型把这理解成了"非必要不用但可以偶尔用"。

我做了一个改动：把"尽量避免"改成"绝对禁止"，加了 ❌→✅ 对照示例。分数直接从 80% 跳到 100%。验证了两轮，稳定。

这里有个 self-evaluation 的偏差需要注意。生成和评估都是同一个模型做的，模型可能"学会了"怎么让自己评高分，但人类读着仍然觉得不对。我后来加了三个更难的 eval 才把新弱点暴露出来。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS** — "不是...而是..." 是在引用/讨论，不是在正文中使用
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — binary eval, self-evaluation, baseline, prompt
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "我给自己的博客 skill 跑了一轮 autoresearch"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我给自己的"、"我做了一个改动"、"我后来加了"
- **Score: 8/8**

---

## Experiment 5 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | Score |
|-----|----------|----|----|----|----|----|----|----|----|-------|
| 1   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 2   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 3   | 代码仓库写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 4   | 续写博客v2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 5   | 调研写博客v2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |

**Total score: 40/40 (100.0%)**

Per-eval breakdown:
- E1-开头无套话: 5/5
- E2-无反模式: 5/5
- E3-语气硬无模糊词: 5/5
- E4-具体工程名词: 5/5
- E5-无重复解释: 5/5
- E6-真实场景开头: 5/5 ← **From 0/5 to 5/5**
- E7-无AI过渡句: 5/5 ← **From 3/5 to 5/5**
- E8-有第一人称工程叙事: 5/5 ← **From 0/5 to 5/5**

**Analysis:** Massive improvement. The three-part mutation (first-person requirements + real-scenario openings + AI transition ban) fixed all three new evals simultaneously. Score jumped from 70% to 100%. The key insight was that E6 and E8 had a common root cause: the skill was steering the model toward documentation-style writing instead of personal blog writing.
