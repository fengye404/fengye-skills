# Experiment 19 — Final Comprehensive Stress Test (Round 10)

## Mutation Applied
Added unified "自检清单" (checklist) section at the end of the skill, consolidating all self-check items into a single actionable list.

## Eval Set (Full 12 — combined hygiene + hard evals)
- E1: 开头无套话
- E2: 无反模式句式 (不是...而是, 换句话说, 值得注意的是, etc.)
- E6: 真实场景开头
- E8: 第一人称工程叙事
- E10: 无AI高频词
- E15: 有随意连接词 (≥2)
- E16: 有口语化表达 (≥2)
- E18: 无三连平行句
- E19: 有弯路叙事
- E20: 有未完美之处
- E21: 有闲话/个人插叙
- E22: 结尾非"不过+遗留"模板

12 evals × 5 runs = 60

---

## Run 1 — 场景1: 续写博客 (JVM GC 调优)

### Output:

前段时间线上一个 Java 服务的 GC 暂停时间偏高，P99 延迟被拉到了 800ms。查了一圈发现是 GC 策略没调好。

这个服务用的 JDK 17，默认 GC 是 G1。Grafana 上看 GC pause time，大部分在 20ms 以内，但每隔几分钟就有一次 Mixed GC 暂停 400-600ms。是 Mixed GC 的老年代回收太重了。

先看了下堆的配置。-Xmx 设的 4G，年轻代没单独配，G1 自动分配大概 60% 给年轻代。问题是老年代里堆了很多长生命周期的对象——本地缓存、连接池、线程池的线程栈引用。这些对象 Mixed GC 的时候要一起扫描和回收。

于是调了两个参数：`-XX:G1MixedGCCountTarget=16`（把 Mixed GC 的次数增加，每次回收的区域减少，单次暂停更短），`-XX:G1HeapWastePercent=10`（降低回收阈值，更早触发回收，避免积攒太多垃圾一次性回收）。

调完之后 Mixed GC 的暂停从 400-600ms 降到了 100-150ms。P99 延迟回到了正常的 200ms 以内。

其实一开始想过直接换 ZGC。ZGC 的暂停时间理论上控制在 1ms 以内，但 ZGC 在低堆内存（4G）的场景下吞吐量会有一些损耗。后来想想算了，调调 G1 参数就够了，没必要为了压暂停时间去换整个 GC。

折腾 GC 这事让我想起当年刚学 Java 的时候——背了一堆 GC 算法的名字（CMS、G1、ZGC、Shenandoah），面试的时候倒背如流，但从来没在生产上调过。这次算是真正用上了。

### Evaluation:
- E1: ✅ — 无套话 | E2: ✅ — 无反模式句式 | E6: ✅ — 线上服务GC暂停时间偏高
- E8: ✅ — "查了一圈"、"我想过"
- E10: ✅ — 无AI高频词 | E15: ✅ — "于是"、"其实"、"后来"
- E16: ✅ — "查了一圈"、"折腾GC这事"、"够了"
- E18: ✅ — 只调了两个参数，不是三连枚举 | E19: ✅ — 弯路："想过换ZGC...算了"
- E20: ✅ — "ZGC在低堆内存场景下吞吐量有损耗" 权衡
- E21: ✅ — "想起当年刚学Java的时候——背了一堆GC算法的名字"
- E22: ✅ — 结尾是个人回忆
- **Score: 12/12**

## Run 2 — 场景2: 调研 (Deno 2.0 值不值得用)

### Output:

Deno 2.0 发布之后看了一下 changelog。最大的变化是完全兼容 npm 了。

说实话之前一直没太关注 Deno。Ryan Dahl 重新做 JS runtime 的故事很酷，但"不兼容 npm"这一条就把 90% 的潜在用户挡在了外面。现在 Deno 2.0 加了 `npm:` 前缀就能直接用 npm 包，这个门槛总算没了。

试了一下在一个小项目里用 Deno 2.0 写 API 服务。选了 Deno 自带的 `Deno.serve` 做 HTTP server，没有用 Express 之类的框架。

```typescript
Deno.serve({ port: 3000 }, async (req) => {
  const url = new URL(req.url);
  if (url.pathname === "/api/hello") {
    return new Response(JSON.stringify({ message: "hello" }), {
      headers: { "content-type": "application/json" },
    });
  }
  return new Response("Not Found", { status: 404 });
});
```

标准的 Web API（Request、Response、URL），没有 Express 那套 req/res 的私有 API。写起来挺清爽的。

TypeScript 直接跑，不用 tsconfig 也不用编译步骤。这点和 Bun 一样爽。

但有个事情让我犹豫要不要在正式项目里用——Deno Deploy 的定位。Deno 公司的商业模式是 Deno Deploy（类似 Cloudflare Workers 的 edge runtime）。这意味着 Deno 的很多设计决策是围绕 edge 场景优化的。如果你的服务跑在传统的 VPS 或 K8s 上，有些 edge 优化反而是限制——比如默认不能读写文件系统（需要显式 `--allow-read` 权限）。

另一个现实问题是招人。找一个会 Node.js 的后端很容易，找一个会 Deno 的就难了。团队里推一个小众 runtime 的阻力比技术本身大得多。这跟当年推 Kotlin 替代 Java 的经历很像——Kotlin 明明更好用，但老板一句"出了问题谁来维护"就把提案打回去了。

反正个人项目我愿意用 Deno。正式项目再等等。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "Deno 2.0发布之后看了一下changelog"
- E8: ✅ — "试了一下"、"让我犹豫"
- E10: ✅ | E15: ✅ — "反正"、"其实"（无其实，但有"说实话"——不在列表里）。搜索：于是/后来/反正/其实/说白了/结果/然后 → 只有"反正"。FAIL (1/2)
- Wait, let me re-read: "说实话之前一直没太关注" — "说实话" 不在列表。"然后" 也没有。 "这跟当年推Kotlin..." — 没有连接词。Hmm. E15: **FAIL** (only 1)
- E16: ✅ — "挺清爽的"、"一样爽"
- E18: ✅ | E19: ✅ — 弯路：Deno好 → 但Deploy定位 + 招人问题 → 个人用
- E20: ✅ — "找一个会Deno的就难了"
- E21: ✅ — "跟当年推Kotlin替代Java的经历很像"
- E22: ✅ — "个人项目我愿意用Deno。正式项目再等等。" 虽然有"再等等"，但格式不是"不过+遗留"
- **Score: 11/12** (E15 FAIL)

## Run 3 — 场景3: 代码仓库 (TermPilot 协议设计)

### Output:

TermPilot 的前后端通信协议改了三版。

第一版最粗暴——前端发的是纯文本（用户在终端里打的字符），relay 收到后直接 pipe 给 PTY。relay 回传的也是纯文本（PTY 的输出）。

够简单，但很快就不够用了。

后来要支持终端窗口 resize——前端需要告诉 relay "我这边的终端变成 120 列 × 30 行了"。如果协议只有纯文本，没办法区分"这是用户输入"还是"这是控制命令"。

于是设计了第二版：JSON 消息格式。每条消息有 `type` 字段，`type: "input"` 是用户输入，`type: "resize"` 是窗口调整，`type: "output"` 是 PTY 输出。

```typescript
interface Message {
  type: 'input' | 'output' | 'resize' | 'heartbeat';
  data?: string;
  cols?: number;
  rows?: number;
}
```

JSON 格式灵活，扩展也方便——后来加 heartbeat、session 管理都是加个新 type 就行。

但有个性能问题。终端输出高频而且数据量大——比如跑一个 `cat` 大文件，每秒钟可能有几十 KB 的输出。每条输出都包一层 JSON `{"type":"output","data":"..."}` 有额外的序列化开销。对于纯文本数据来说，JSON 的转义处理（引号、换行符）也是负担。

其实对于 TermPilot 这个量级的应用来说，这点开销完全可以忽略。但我还是花了一个晚上搞了第三版——对 output 类型使用 binary frame 直接传 raw bytes，其他类型继续用 JSON。WebSocket 本身就支持 text frame 和 binary frame 的混用，做起来不复杂。

折腾完之后测了一下，大文件 cat 的传输速度确实快了 20% 左右。虽然这个优化在实际使用中基本感受不到——用户不会天天在远程终端上 cat 大文件。

这种"没什么用但就是想优化"的冲动让我想起以前写课设的时候，明明功能已经够得分了，非要把冒泡排序换成快排。本质上是一种做无用功的快乐。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "TermPilot的前后端通信协议改了三版"
- E8: ✅ — "我还是花了一个晚上"
- E10: ✅ | E15: ✅ — "后来"、"于是"、"其实"
- E16: ✅ — "最粗暴"、"折腾完"、"做无用功的快乐"
- E18: ❌ — "第一版...第二版...第三版..." — 三连平行枚举？检查：不是严格的平行句式。"第一版最粗暴"开始、"于是设计了第二版"、"还是花了一个晚上搞了第三版"——每个版本的开篇方式不同，且中间有大量展开。第一版和第二版之间有"够简单但不够用了"和"后来要支持resize"的叙事过渡。PASS——这是按时间顺序讲迭代过程，不是平行列举。
- E19: ✅ — 弯路：纯文本 → JSON → binary (不断迭代)
- E20: ✅ — "这个优化在实际使用中基本感受不到"
- E21: ✅ — "想起以前写课设的时候...把冒泡排序换成快排"
- E22: ✅ — "本质上是一种做无用功的快乐" 自嘲结尾
- **Score: 12/12**

## Run 4 — 场景1: 续写博客 (数据库连接池踩坑)

### Output:

上周生产环境出了一次数据库连接池耗尽的故障。持续了二十分钟，影响了所有读写请求。

现象是所有 API 开始返回 500，日志里刷满了 `HikariPool-1 - Connection is not available, request timed out after 30000ms`。

先看 HikariCP 的配置：maximum-pool-size 是默认的 10。这个服务的并发量其实不高，正常情况下 10 个连接绰绰有余。

于是排查是不是有连接泄露——某个代码路径拿了连接但没释放。HikariCP 有个配置 `leak-detection-threshold`，设了 30 秒，意思是一个连接如果被持有超过 30 秒就打 warning 日志。

翻日志果然找到了：有一个定时任务在遍历数据做批量更新，每条记录单独开一个事务。处理到某些异常数据的时候，事务卡住了——外部 API 调用超时，默认超时时间是 60 秒。这一个事务占了一个连接 60 秒，定时任务里有多条并发，连接池很快就被占满了。

改了两个地方。第一个是给外部 API 调用加了 5 秒超时。第二个是把定时任务的事务拆小——原来是每调一条数据开一个 @Transactional 方法，改成每 50 条一批、批内一个事务。这样即使某条失败了，其他批次不受影响，连接也能及时释放。

其实 HikariCP 的 maximum-pool-size 也应该调大一点。10 个连接对于有外部 API 调用的服务来说偏少——一旦外部服务变慢，连接被占用的时间就会变长。后来设成了 20。

折腾这事的时候突然想起第一次学数据库的时候根本不知道什么是连接池，直接每次请求 `DriverManager.getConnection()` 拿连接。能跑但性能烂到什么程度呢——本地开发都要等一秒才能返回结果。那时候还以为是 SQL 的问题。

连接池从 10 调到 20，超时从 60 调到 5。就这么点改动。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "上周生产环境出了一次数据库连接池耗尽的故障"
- E8: ✅ — "先看配置"、"翻日志"
- E10: ✅ | E15: ✅ — "于是"、"其实"、"后来"
- E16: ✅ — "折腾这事"、"绰绰有余"、"能跑但性能烂到什么程度呢"
- E18: ✅ — "改了两个地方" — 只有 2 个，不到 3 个 | E19: ✅ — 弯路：以为10够用 → 外部API超时占住连接
- E20: ✅ — 隐含外部服务变慢仍可能是问题
- E21: ✅ — "想起第一次学数据库的时候根本不知道什么是连接池"
- E22: ✅ — "连接池从10调到20，超时从60调到5。就这么点改动。" 干脆结尾
- **Score: 12/12**

## Run 5 — 场景2: 调研 (Cloudflare Workers 能不能当后端用)

### Output:

最近在看 Cloudflare Workers 能不能拿来当 API 后端用。结论是：能用，但得接受一些限制。

起因是个人项目需要一个简单的 API 服务——接收 webhook、处理一下数据、存到 D1（Cloudflare 的 SQLite 数据库）。不想为了这么点功能租一个 VPS。

Workers 跑在 Cloudflare 的 edge 节点上，冷启动几乎没有（不像 AWS Lambda 那种容器冷启动要等几百毫秒）。代码推送也很快——`wrangler deploy` 一下就完事。

写了个简单的 API：

```typescript
export default {
  async fetch(request: Request, env: Env) {
    if (request.method === 'POST' && new URL(request.url).pathname === '/webhook') {
      const body = await request.json();
      await env.DB.prepare('INSERT INTO events (data) VALUES (?)')
        .bind(JSON.stringify(body))
        .run();
      return new Response('OK');
    }
    return new Response('Not Found', { status: 404 });
  }
};
```

跑起来挺好的。D1 的 SQL 写法和普通 SQLite 一样，学习成本几乎为零。

然后就开始遇到限制了。

Workers 单次执行时间限制是 30 秒（免费版）。如果要处理的逻辑稍微复杂一点——比如调多个外部 API 再聚合结果——很容易超时。而且 Workers 运行在 V8 isolate 里，不是 Node.js 环境。`fs`、`child_process` 这些 Node API 全都没有。有些 npm 包用了这些 API 就直接挂了。

反正对于我这个需求（接 webhook + 存数据库）来说完全够用。比起租一个月 5 刀的 VPS 维护一个 Node 服务，Workers 的免费额度（每天 100k 请求）绰绰有余。

这种"轻量级后端"的体验让我想到以前用 LeanCloud 写作业的日子。那时候也是不想管服务器，直接把数据存 LeanCloud 的 BaaS 里。后来 LeanCloud 涨价了，才被迫学了怎么自己搭服务器。技术选型这事，便宜和好用往往只能选一个。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "最近在看Cloudflare Workers能不能拿来当API后端用"
- E8: ✅ — "个人项目需要"
- E10: ✅ | E15: ✅ — "反正"、"然后"
- E16: ✅ — "一下就完事"、"挺好的"、"直接挂了"、"绰绰有余"
- E18: ✅ | E19: ✅ — 弯路：跑起来好 → 遇到限制（超时和Node API不可用）
- E20: ✅ — "30秒限制"、"npm包可能直接挂"
- E21: ✅ — "想到以前用LeanCloud写作业的日子...后来LeanCloud涨价了"
- E22: ✅ — "便宜和好用往往只能选一个" 感慨结尾
- **Score: 12/12**

---

## Experiment 19 Summary

| Run | E1 | E2 | E6 | E8 | E10 | E15 | E16 | E18 | E19 | E20 | E21 | E22 | Score |
|-----|----|----|----|----|-----|-----|-----|-----|-----|-----|-----|-----|-------|
| 1 GC调优 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 12/12 |
| 2 Deno 2.0 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 11/12 |
| 3 协议设计 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 12/12 |
| 4 连接池 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 12/12 |
| 5 Workers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 12/12 |

**Total: 59/60 (98.3%)**

**Only failure:** E15 in Run 2 — used only "反正" (1 connector instead of ≥2). Minor intermittent issue.

**Decision: KEEP** — 98.3% on 12-eval comprehensive test. Round 10 complete.

---

# FINAL RESULTS

## Optimization Summary (10 Rounds, 10 Mutations)

| Round | Exp | Score | Mutation |
|-------|-----|-------|----------|
| 1 | 0-3 | 70→95% | 反模式句式硬禁止 + 模糊词禁止 |
| 2 | 4-7 | 70→100% | 第一人称视角 + 真实场景开头 + AI过渡句禁止 |
| 3 | 8-9 | 82.9→100% | 句子节奏 + 段落结构 + AI高频词禁止 |
| 4 | 10 | 100% | 新增E12/E13/E14更难eval |
| 5 | 11-12 | 82.2→100% | 口语化语气（连接词+口语表达+对比表） |
| 6 | 13-14 | 95.6→100% | 禁止平行枚举 |
| 7 | 15-16 | 95.6→91.1% | 结尾多样化 + 个人闲话 |
| 8 | 17 | 93.3% | E15自检强化 |
| 9 | 18 | 100% | E18/E21自检强化 |
| 10 | 19 | 98.3% | 统一自检清单 |

## Eval Evolution
- Started with 5 basic evals → grew to 12 comprehensive evals
- 3 rounds of eval hardening (E9→E14, E15→E16, E18→E23)
- Final eval set covers: hygiene (E1/E2), structure (E6/E10), voice (E8/E15/E16), anti-AI patterns (E18/E19/E20/E21/E22)

## Key Skill Additions (0.0.1 → 0.0.2)
1. 反模式: "尽量避免" → "绝对禁止" + extensive ❌→✅ examples
2. 视角与语气: NEW — first-person engineering narrative required
3. 句子节奏: NEW — ≥3 short sentences (≤8 chars), break medium-length monotony
4. 口语化语气: NEW — casual connectors (≥2), colloquial expressions (≥2), AI vs human comparison table
5. 段落结构: NEW — non-uniform paragraphs, 1-2 sentence paragraphs required
6. 禁止平行枚举: NEW — no 3+ consecutive parallel sentences
7. 个人闲话: NEW — personal asides/tangents required
8. 结论: Rewritten — anti-template endings, variety required
9. 引言: Rewritten — real-scenario opening required, abstract concepts banned
10. 自检清单: NEW — unified post-writing checklist
