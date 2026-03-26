# Experiment #8 — Round 3 Baseline (Anti-AI Evals)

## Eval Changes
Replaced saturated E3/E4/E5/E7 with harder evals:
- E9: 句长节奏变化 (sentence rhythm variety)
- E10: 无AI高频词 (no AI vocabulary)
- E11: 有非匀称段落 (has short 1-2 sentence paragraphs)

Active evals: E1, E2, E6, E8, E9, E10, E11

---

## Run 1 — 场景1: 续写博客（Kafka 消费者组 rebalance）

### Output:

最近在调一个 Kafka 消费者延迟问题，发现根本原因是 rebalance 风暴。

我们的消费者组有 12 个实例，每个实例订阅同一个 topic 的不同 partition。正常情况下每个实例分到 3-4 个 partition。但每次有实例重启（比如发版），整个消费者组会触发 rebalance——所有实例停止消费，等待重新分配 partition，分配完再恢复。

问题在于 rebalance 期间所有消费者都是停的。12 个实例轮流发版，如果每次 rebalance 耗时 30 秒，发版过程中消费者组可能有好几分钟的累计停顿。积压的消息越来越多，监控面板上延迟曲线像锯齿一样。

解决方案是开启 Cooperative Sticky Assignor。默认的 Range Assignor 在 rebalance 时会先撤销所有 partition 再重新分配。Cooperative Sticky 的策略是增量式的——只迁移需要移动的 partition，其他 partition 的消费不中断。

配置改动就一行：

```properties
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
```

改完之后 rebalance 期间的消费中断从 30 秒降到了 2-3 秒。但有个前提：消费者组里所有实例必须同时使用 Cooperative Sticky，不能混用。灰度发版时如果新旧实例用不同的 assignor，会触发更严重的 rebalance 错误。所以这个配置变更要一次性全量推。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "最近在调一个 Kafka 消费者延迟问题"
- E8 第一人称: **PASS** — "我们的消费者组"
- E9 句长变化: **FAIL** — 句子大多在 20-35 字范围，没有明显的 ≤8字短句
- E10 无AI高频词: **PASS** — 未出现禁止词汇
- E11 非匀称段落: **FAIL** — 所有段落都是 3+ 句完整论证，无短段落
- **Score: 5/7**

---

## Run 2 — 场景2: 调研写博客（WebAssembly 在后端的应用）

### Output:

上个月看到 Figma 把部分后端逻辑从 TypeScript 迁到了 Rust + Wasm，性能提升了 10 倍。我想搞清楚 WebAssembly 在后端到底能做什么，花了一周时间调研。

WebAssembly 最初是为浏览器设计的，但 WASI（WebAssembly System Interface）的出现让它可以脱离浏览器独立运行。WASI 提供了文件系统访问、网络、环境变量等标准化接口，Wasm 模块通过 WASI 和操作系统交互。

后端使用 Wasm 的典型场景是插件系统。Shopify 的 Function 平台让商家用 Wasm 编写自定义业务逻辑，跑在 Shopify 的服务器上。Wasm 的沙箱隔离天然解决了安全问题——插件代码无法直接访问宿主机的文件系统和网络。

另一个场景是边缘计算。Cloudflare Workers、Fastly Compute 都支持 Wasm 模块。启动时间是 Wasm 的核心优势——冷启动在微秒级别，Docker 容器的冷启动是秒级。对于延迟敏感的边缘场景，这个差距很关键。

我试着用 Rust 写了一个 URL 路由匹配模块编译成 Wasm，跑在 wasmtime 上。性能确实比等价的 Node.js 实现快了 5-8 倍。但开发体验不好——Rust 的编译时间长，调试工具不成熟，生态库和 WASI 的兼容性参差不齐。

目前的判断：Wasm 在后端的定位是"性能敏感的热路径"和"需要沙箱隔离的插件系统"。把整个后端服务用 Wasm 重写没有必要。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — 从看到 Figma 案例开始
- E8 第一人称: **PASS** — "我想搞清楚"、"我试着用 Rust 写了"
- E9 句长变化: **FAIL** — 句子均匀在 20-40 字，缺少短句
- E10 无AI高频词: **FAIL** — "天然解决了"、"核心优势" — 含"天然"
- E11 非匀称段落: **FAIL** — 最后一段2句，但其他段全是3+句。勉强 PASS... 不，最后一段确实只有2句。**PASS**
- **Score: 5/7**

Wait, let me re-evaluate E11. "目前的判断：Wasm 在后端的定位是...把整个后端服务用 Wasm 重写没有必要。" — This is 2 sentences. **PASS for E11**.

Revised:
- E11 非匀称段落: **PASS** — 最后一段只有2句
- **Score: 5/7**

---

## Run 3 — 场景3: 代码仓库写博客（TermPilot agent 设计）

### Output:

TermPilot 的 agent 模块是整个项目里改动最频繁的部分，从开始到现在重写了两次。

第一版 agent 很简单：接收用户消息，调 LLM API 生成命令，通过 relay 执行。没有状态管理，没有上下文窗口控制，每次调用都是独立的。问题很快暴露——agent 不记得之前执行过什么命令，产生了重复操作。

第二版加了对话历史管理和工具调用抽象。agent 维护一个消息队列，每次调用 LLM 时把最近 N 条消息作为上下文传入。工具定义用 JSON Schema 描述，和 OpenAI 的 function calling 格式一致。

工具列表目前有五个：`execute_command`、`read_file`、`write_file`、`search_code`、`get_terminal_output`。每个工具有参数 schema，agent 按 schema 构造参数，relay 校验后执行。这个设计的好处是加新工具只需要在 `shared/src/tools.ts` 里定义 schema，不需要改 agent 的核心逻辑。

上下文窗口是个持续要调的参数。太短 agent 会忘记之前做了什么，太长 token 成本高而且 LLM 容易在长上下文里"走神"。目前设的是最近 20 条消息，超出后按 FIFO 丢弃最早的消息。后续打算做更智能的压缩——把早期消息用 summary 替代。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 的 agent 模块是整个项目里改动最频繁的部分"
- E8 第一人称: **PASS** — "从开始到现在重写了两次"，暗示第一人称
- E9 句长变化: **FAIL** — 依然没有≤8字的短句
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **FAIL** — 所有段落都是3+句
- **Score: 5/7**

---

## Run 4 — 场景1: 续写博客（MySQL 大表加字段）

### Output:

上周给一张 2 亿行的 MySQL 表加了个字段，踩了几个坑。

直觉是用 `ALTER TABLE ... ADD COLUMN`，但在 InnoDB 里对大表做 DDL 会锁表。MySQL 8.0 引入了 Instant DDL，部分 ALTER 操作可以在毫秒级完成而不锁表。加字段属于支持 Instant 的操作——前提是新字段加在表的最后一列。

我试了一下：

```sql
ALTER TABLE orders ADD COLUMN extra_info VARCHAR(256) DEFAULT NULL, ALGORITHM=INSTANT;
```

在测试环境秒级完成。但生产环境执行时报错了：`ERROR 1846: ALGORITHM=INSTANT is not supported`。排查后发现生产环境的 MySQL 版本是 8.0.12，Instant DDL 是 8.0.29 才加的。版本差了一大截。

回退到传统方案：用 pt-online-schema-change。原理是创建一张新表（包含新字段），用触发器把原表的增量写同步到新表，后台慢慢把历史数据拷过去，最后原子性地 rename。

整个过程跑了大概 4 个小时。期间对线上几乎无感知——pt-online-schema-change 会控制每次拷贝的行数和间隔，避免打满 IO。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "上周给一张 2 亿行的 MySQL 表加了个字段"
- E8 第一人称: **PASS** — "我试了一下"
- E9 句长变化: **PASS** — "版本差了一大截。" (8字)，有短句！同时有长句
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "我试了一下：" 后面跟代码块，这段就一句话+代码
- **Score: 7/7**

---

## Run 5 — 场景2: 调研写博客（Bun vs Node.js）

### Output:

最近项目里有个 CLI 工具启动特别慢，Node.js 冷启动要 800ms，用户每次敲命令都要等。同事建议试试 Bun。

Bun 是 Zig 写的 JavaScript runtime，主打启动快和内置工具链。它自带 bundler、test runner、package manager，不需要额外装 webpack 或 vitest。

实测结果：同一个 CLI 工具在 Bun 下冷启动 120ms，提升明显。但跑项目的完整测试套件时遇到了兼容性问题。我们用了 `node:child_process` 的 `execSync`，Bun 的实现和 Node.js 有细微差异——某些 shell 命令的退出码处理不一致。

另外 Bun 的 Node.js API 兼容性还没达到 100%。我们依赖的 `node:cluster` 模块在 Bun 里直接报 not implemented。对于新项目或者简单的 CLI 工具，Bun 启动速度的优势很明显。但对已有的 Node.js 项目，迁移成本取决于你用了多少 Node.js 特有的 API。

我最后的选择是：CLI 工具单独用 Bun 跑，主服务继续用 Node.js。两套 runtime 并行，互不影响。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — 从项目里 CLI 启动慢的真实问题切入
- E8 第一人称: **PASS** — "我们用了"、"我最后的选择是"
- E9 句长变化: **FAIL** — "提升明显。" (5字) 有短句，BUT 没有明显的≥35字长句... 实际上 "我们用了 `node:child_process` 的 `execSync`，Bun 的实现和 Node.js 有细微差异——某些 shell 命令的退出码处理不一致。" 这句约45字。**PASS**
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — 最后一段只有 2 句
- **Score: 7/7**

---

## Experiment 8 Summary

| Run | Scenario | E1 | E2 | E6 | E8 | E9 | E10 | E11 | Score |
|-----|----------|----|----|----|----|----|----|-----|-------|
| 1   | Kafka rebalance | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | 5/7 |
| 2   | Wasm后端 | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | 5/7 |
| 3   | TermPilot agent | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | 5/7 |
| 4   | MySQL加字段 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |
| 5   | Bun vs Node | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |

**Total: 29/35 (82.9%)**

Per-eval:
- E1: 5/5, E2: 5/5, E6: 5/5, E8: 5/5
- E9 句长变化: 2/5 ← **主要失败点**
- E10 无AI高频词: 4/5
- E11 非匀称段落: 3/5

**Analysis:** E1/E2/E6/E8 全部保持（前两轮优化成果牢固）。新 eval 揭示：
1. E9 (2/5)：模型倾向于写均匀中等长度的句子，缺少短促有力的断句
2. E11 (3/5)：模型倾向于每段都写成完整论证，不会写"一句话就是一段"的粗糙感
3. E10 (4/5)："天然"一词仍偶尔出现
