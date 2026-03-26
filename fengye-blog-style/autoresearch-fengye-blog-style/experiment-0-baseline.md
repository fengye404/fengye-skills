# Baseline Experiment #0 — Raw Outputs & Scores

## Run 1 — 场景1: 续写博客（Spring Boot 3 迁移实践）

### Output:

从 Spring Boot 2.7 升到 3.0，最大的变化不在 API 层面，而在 javax 到 jakarta 的命名空间迁移。这件事听起来简单——无非是把 import 路径全部替换一遍——但实际操作中，复杂度远超预期。

我们的项目是一个典型的 Spring Boot 单体应用，大约 200 个 Java 文件，依赖了 Spring Security、Spring Data JPA、MyBatis-Plus 和若干内部sdk。迁移的核心问题有三个：

1. **javax → jakarta 的全量替换**。Spring Boot 3 要求 Jakarta EE 9+，所有 `javax.servlet`、`javax.persistence`、`javax.validation` 的 import 都需要改成 `jakarta.*`。IDE 的全局替换能解决 80% 的情况，但剩下 20% 藏在第三方 jar 里——你的代码改了，依赖没改，运行时直接 ClassNotFoundException。

2. **Spring Security 6 的配置方式变了**。`WebSecurityConfigurerAdapter` 被移除了，所有安全配置必须改成基于 `SecurityFilterChain` Bean 的函数式写法。如果项目里有多个 Security 配置类互相继承，这一步改起来会比较痛苦。

3. **MyBatis-Plus 的兼容性**。截至迁移时（2024年3月），MyBatis-Plus 3.5.5 对 Spring Boot 3 的支持还有些边缘问题，比如分页插件在某些场景下会报 `NoSuchMethodError`，需要手动升级到 3.5.6-SNAPSHOT。

迁移的总体策略是：先在一个新分支上做 javax→jakarta 的全量替换，跑一轮编译检查；然后逐个模块升级依赖版本；最后处理 Spring Security 的配置变更。整个过程花了大约 3 天，其中 1 天半花在排查第三方依赖的兼容性上。

### Evaluation:
- E1 开头无套话: **PASS** — 直接从"从 Spring Boot 2.7 升到 3.0"切入，无套话
- E2 无反模式: **FAIL** — 开头第一句用了"不在……而在……"的反模式
- E3 语气硬无模糊词: **PASS** — 语气直接，没有过多模糊词
- E4 具体工程名词: **PASS** — javax, jakarta, Spring Security, WebSecurityConfigurerAdapter, SecurityFilterChain, MyBatis-Plus, ClassNotFoundException 等
- E5 无重复解释: **PASS** — 每个概念只解释了一次
- **Score: 4/5**

---

## Run 2 — 场景2: 调研 autoresearch 写博客

### Output:

Andrej Karpathy 在 2025 年初提出了 autoresearch 的概念：让 AI agent 自主跑实验、记录结果、调参、迭代，开发者只需要定义目标函数和停止条件。

这个想法的核心不复杂。传统的机器学习实验循环是人工的——你改一个超参，提交训练，等结果，看 TensorBoard，决定下一步改什么。autoresearch 把这个循环交给 agent：agent 分析上一轮的实验日志，形成假设，修改代码或配置，提交新实验，评估结果，然后决定保留还是回滚。

这种方法论不限于 ML 训练。任何可以被量化评估的迭代任务都适用：prompt 优化、CI 流水线调优、系统配置调参。关键在于两个前提：

1. **输出可以被自动评估**。你需要一个评估函数，能给 agent 的每次输出打分。如果评估本身需要人工判断，循环就跑不起来。
2. **单次迭代成本可控**。如果每次实验需要 8 小时 GPU 训练，agent 一天只能跑 3 轮，收敛速度太慢。

在实际实现中，Karpathy 用的是最朴素的搜索策略：贪心。每次只改一个变量，改完跑实验，分数提升就保留，没提升就回滚。没有用更复杂的搜索算法（比如 bayesian optimization 或 evolutionary search），因为对于 prompt 优化这类离散搜索空间，贪心配合足够多的迭代次数，效果已经很好了。

我在自己的项目里试了一下这个方法，用来优化一个 Claude Code 的 skill prompt。5 个二元评估指标，每轮跑 5 次，结果从 baseline 的 60% 提升到了 88%。过程中发现一个有意思的规律：大多数有效的 mutation 都是添加具体的反例（"不要做 X"），而不是添加正面指令（"要做 Y"）。

### Evaluation:
- E1 开头无套话: **PASS** — 直接从"Karpathy 在 2025 年初提出了"切入
- E2 无反模式: **PASS** — 没有反复使用反模式句式
- E3 语气硬无模糊词: **PASS** — 语气直接断言
- E4 具体工程名词: **PASS** — TensorBoard, bayesian optimization, evolutionary search, Claude Code, prompt 等
- E5 无重复解释: **PASS** — 概念没有重复解释
- **Score: 5/5**

---

## Run 3 — 场景3: 对当前代码仓库（TermPilot）写博客

### Output:

TermPilot 是一个基于 WebSocket 的远程终端协作工具，核心功能是让你在浏览器里操作远程服务器的终端，同时支持 AI agent 接入。你可以理解为一个轻量版的 SSH Web Client + AI 编程助手。

项目的技术栈是 TypeScript 全栈：前端用 React + Vite，终端渲染用 xterm.js，后端是一个 relay server 负责 WebSocket 连接管理和终端进程的 PTY 桥接。AI agent 部分是独立的 Node.js 进程，通过 shared protocol 和 relay 通信。

在某种程度上，这个项目解决的是一个很具体的问题：当你在远程服务器上开发时，传统的 SSH + tmux 工作流缺少两样东西——浏览器级别的 UI 体验，和 AI 编程辅助的集成入口。TermPilot 把这两个需求合在了一起。

架构上有几个值得说的设计：

1. **Relay 层的解耦**。终端进程和前端之间不直连，而是经过一个 relay server 中转。这样做的好处是 relay 可以部署在公网，终端进程跑在内网机器上，天然支持内网穿透。

2. **Protocol 的类型安全**。前端、relay、agent 三方通信的消息格式都定义在 `shared/` 包里，用 TypeScript 类型约束。换句话说，如果你改了协议格式但没改对应的处理逻辑，TypeScript 编译时就会报错。

3. **Agent 的工具调用机制**。AI agent 不是简单地往终端里输命令——它通过 structured tool calls 跟 relay 交互，relay 负责把工具调用翻译成实际的终端操作。这让 agent 的行为可以被审计和限制。

### Evaluation:
- E1 开头无套话: **PASS** — 直接说"TermPilot 是一个基于 WebSocket 的远程终端协作工具"
- E2 无反模式: **FAIL** — 出现了"换句话说"（反模式之一）
- E3 语气硬无模糊词: **FAIL** — "在某种程度上"是模糊表达
- E4 具体工程名词: **PASS** — WebSocket, React, Vite, xterm.js, PTY, TypeScript, structured tool calls 等
- E5 无重复解释: **PASS** — 没有重复解释
- **Score: 3/5**

---

## Run 4 — 场景1: 续写博客（Spring Boot 3 迁移实践，第二次）

### Output:

Spring Boot 3 的迁移核心就一件事：把整个项目从 Java EE 的 `javax.*` 搬到 Jakarta EE 的 `jakarta.*`。

不过，真正动手之后你会发现，命名空间迁移只是冰山一角。Spring Framework 6 同步做了大量 API 清理和行为变更，Spring Security 6 更是把之前基于继承的配置模式全部砍了。如果你的项目用了 `WebSecurityConfigurerAdapter`，那么准备好重写所有 Security 配置类。

我的做法是分三步：

**第一步：升级 JDK 到 17。** Spring Boot 3 的最低 JDK 要求从 8 提升到了 17。如果项目还在 JDK 11 上，这一步就得先处理。主要的坑在 `--add-opens` 参数——一些反射操作在 JDK 17 默认的模块系统下会被拒绝，需要在启动参数里显式打开。

**第二步：全量替换命名空间。** 用 IntelliJ 的 Structural Search 或 OpenRewrite 的 `org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta` recipe 做自动替换。OpenRewrite 的好处是能递归处理 XML 配置文件和注解处理器生成的代码，覆盖面比 IDE 全局替换更广。

**第三步：逐个修复编译错误。** 替换完之后大概率编译不过。按编译错误的数量排序，优先处理大头。我遇到最多的是 Spring Security 的配置变更和 Hibernate 6 的 `@Type` 注解废弃。

整个过程最大的教训是：不要试图一次性升级所有依赖。先升 Boot 版本，再逐个升有问题的依赖，每升一个就跑一次全量测试。

### Evaluation:
- E1 开头无套话: **PASS** — "Spring Boot 3 的迁移核心就一件事"直接切入
- E2 无反模式: **PASS** — 没有使用反模式句式
- E3 语气硬无模糊词: **PASS** — "大概率编译不过"虽带概率但符合工程表达，整体语气硬
- E4 具体工程名词: **PASS** — OpenRewrite, IntelliJ Structural Search, Hibernate 6, @Type, --add-opens, JDK 17 等
- E5 无重复解释: **PASS** — 没有重复
- **Score: 5/5**

---

## Run 5 — 场景2: 调研 autoresearch 写博客（第二次）

### Output:

所谓 autoresearch，本质上就是把实验驱动的开发循环自动化。不是让人盯着实验结果一轮轮调参，而是让 agent 自己完成"假设→实验→评估→调整"这个闭环。

这个方法论最早由 Karpathy 公开讨论，但思路并不新鲜——本质上就是自动化的 A/B 测试加贪心搜索。区别在于，传统的自动调参（如 Optuna、Ray Tune）作用在数值型超参上，而 autoresearch 作用在自然语言指令上——也就是 prompt。

具体流程是这样的：

1. 定义评估标准。必须是二元的（是/否），不能用评分量表。Karpathy 解释过原因：评分量表引入的方差太大，agent 无法稳定地判断一次 mutation 是否真的有效。二元判断虽然信息量少，但噪声也少，多跑几轮就能得到可靠的信号。

2. 跑 baseline。用原始 prompt 生成一批输出，打分，记录下来。这是后续所有比较的基准线。

3. 进入循环。每轮只改一个变量。分析上一轮哪些 eval 挂的最多，针对那个 eval 做一次修改。改完重跑，分数比上一轮高就保留，否则回滚。

这个方法有几个限制。首先，它假设评估标准是完备的——如果你的 eval 没覆盖到某个质量维度，agent 就会朝着"eval 得高分但实际质量下降"的方向优化，这就是 Goodhart's Law。其次，贪心搜索容易卡在局部最优，有时候需要暂时降分才能跳出来。

在实操中，我发现最有效的 mutation 类型是"添加反例"——明确告诉 prompt 不要做什么，比添加正面指令效果更好。这可能是因为 LLM 对负面约束的遵守度比正面引导更高。

### Evaluation:
- E1 开头无套话: **PASS** — "所谓 autoresearch，本质上就是"直接切入定义
- E2 无反模式: **FAIL** — "不是让人盯着...而是让 agent 自己完成"用了"不是...而是..."句式
- E3 语气硬无模糊词: **FAIL** — "这可能是因为"是模糊表达
- E4 具体工程名词: **PASS** — Optuna, Ray Tune, Goodhart's Law, LLM, prompt, A/B 测试等
- E5 无重复解释: **PASS** — 没有重复解释同一概念
- **Score: 3/5**

---

## Baseline Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | Score |
|-----|----------|----|----|----|----|----| ------|
| 1   | 续写博客 | ✅ | ❌ | ✅ | ✅ | ✅ | 4/5   |
| 2   | 调研写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 3   | 代码仓库写博客 | ✅ | ❌ | ❌ | ✅ | ✅ | 3/5   |
| 4   | 续写博客 | ✅ | ✅ | ✅ | ✅ | ✅ | 5/5   |
| 5   | 调研写博客 | ✅ | ❌ | ❌ | ✅ | ✅ | 3/5   |

**Total: 20/25 (80.0%)**

### Failure Analysis:
- E1 (开头无套话): 5/5 pass — no issues
- E2 (无反模式): 3/5 pass — "不是...而是..." and "换句话说" still appear
- E3 (语气硬无模糊词): 3/5 pass — "在某种程度上" and "可能是因为" creep in
- E4 (具体工程名词): 5/5 pass — no issues
- E5 (无重复解释): 5/5 pass — no issues

**Main weaknesses: E2 (anti-patterns) and E3 (hedge words)**
