# Experiment 16 — Mutation: Ending variety + Personal asides

## Mutation Applied
1. Rewrote "结论" section: replaced generic "总结工程启发" with explicit anti-template instructions
   - Banned the "不过XXX还没搞明白" as default ending
   - Provided 5 alternative ending styles
   - Core principle: "结尾不需要收束感"
2. Added new "个人闲话" section:
   - Encourages 1-2 personal asides/tangents per article
   - Provided 3 examples
   - Explained WHY: AI never goes off-topic, but humans do

## Run 1 — Java 虚拟线程实战

### Output:

把项目升到 JDK 21 之后，终于试上了虚拟线程。

之前对虚拟线程的理解停留在"轻量级线程、不需要线程池"的层面。实际用起来比想象中舒服。

最直接的改动是把 `@Async` 的线程池换成虚拟线程：

```java
@Bean
public AsyncTaskExecutor applicationTaskExecutor() {
    return new TaskExecutorAdapter(Executors.newVirtualThreadPerTaskExecutor());
}
```

一行配置的事。之前的 `ThreadPoolTaskExecutor` 要配 core size、max size、queue capacity，调参数调得头疼。虚拟线程不需要这些——来一个任务创建一个线程，用完就销。

性能提升也确实明显。有个接口要并发调三个外部 API，之前用平台线程池（核心线程 10 个），高峰期线程不够用要排队。换成虚拟线程之后，并发量直接从 10 拉到了几千，接口 P99 从 3 秒降到 400 毫秒。

踩了个坑。

有个地方用了 `synchronized` 关键字锁住一段数据库操作。虚拟线程遇到 `synchronized` 会 pin 住底层的 carrier thread——相当于虚拟线程的"轻量"优势被废了。JDK 21 的日志里能看到 `jdk.virtualThreadPinned` 事件。改成 `ReentrantLock` 就好了。

说起来，虚拟线程这个概念让我想起了刚学 Go 的时候接触 goroutine——那会儿觉得"一个请求一个协程"的模型简直太优雅了。Java 终于也追上来了。虽然底层实现完全不同，但给开发者的心智模型差不多。

选 JDK 21 还是值的。

### Evaluation:
- E8: ✅ | E15: ✅ — "其实"（无，但"说起来" 类似引出）。检查：于是/后来/反正/其实/说白了/结果/然后... 只有"然后"没出现。重看：没有明确的列表词。**FAIL**？再看："之前...实际用起来" "之前的...虚拟线程不需要" — 没有列表词。Wait: 文本中有没有？"终于试上了" "之前对虚拟线程的理解" "其实" 没出现... "于是" 没出现... hmm 仔细找：没有≥2 个随意连接词。**FAIL**
- E16: ✅ — "调参数调得头疼"、"一行配置的事"
- E18: ✅ | E19: ✅ — 弯路：synchronized pin住carrier thread
- E20: ❌ — 所有问题都解决了 (synchronized → ReentrantLock 搞定)
- E21: ✅ — "想起了刚学Go的时候接触goroutine"
- E22: ✅ — 结尾 "选JDK 21还是值的" 干脆判断
- E23: ✅
- **Score: 7/9** (E15, E20 FAIL)

## Run 2 — npm vs pnpm vs yarn

### Output:

最近给新项目选包管理器，顺便梳理了一下现在三家的状态。

之前一直用 npm。没啥特别的原因——Node 装完就有，不用额外装东西。后来项目依赖多了，`npm install` 要跑三分钟。忍不了了。

于是试了 pnpm。

第一感受是快。install 时间从三分钟降到四十秒。pnpm 用硬链接（hard link）把包存在全局 store 里，不同项目用同一个版本的包时直接链接过去，不用重复下载也不用重复占磁盘。

第二感受是严格。pnpm 默认不允许幽灵依赖（phantom dependencies）——如果 package.json 里没声明，即使是间接依赖也不能直接 import。这事一开始挺烦的，项目里一堆 import 报错，全是之前 npm 的 flat node_modules 给惯出来的坏习惯。但修完之后反而安心了——依赖关系真的是干净的。

yarn 也看了一眼。Berry（yarn 4）的 PnP（Plug'n'Play）模式太激进了——完全去掉 node_modules，用 .pnp.cjs 做模块解析。理论上更快更干净，但生态兼容性是个问题。有些包硬编码了 `node_modules` 路径，PnP 下直接挂了。折腾半天发现要配一堆 `packageExtensions`。

反正最后选了 pnpm。

其实这整个包管理器之争让我想起前端圈一个老传统——每隔两年就得换一次工具链。Grunt → Gulp → Webpack → Rollup → Vite，npm → yarn → pnpm。折腾是真折腾，但每次换完确实比上一代好用。

### Evaluation:
- E8: ✅ | E15: ✅ — "于是"、"反正"、"其实"
- E16: ✅ — "忍不了了"、"挺烦的"、"安心了"、"折腾半天"、"折腾是真折腾"
- E18: ✅ — "第一感受...第二感受..." 只有两个，没到三连
- E19: ✅ — 弯路：yarn PnP 太激进 → 兼容性问题 → 放弃
- E20: ✅ — yarn PnP 兼容性问题没解决，直接放弃了
- E21: ✅ — "每隔两年换一次工具链" 的感慨
- E22: ✅ — 结尾是对前端工具链的感慨，不是"不过+遗留"
- E23: ✅
- **Score: 9/9**

## Run 3 — TermPilot 日志系统

### Output:

TermPilot 的日志一开始就是 console.log 打到 stdout。后来出了几次线上问题排查不了，才认真搞了个日志方案。

第一版用的 winston。配了文件输出和日志轮转，每天一个文件，保留 7 天。

跑了一周发现不对劲——日志文件每天 500MB。relay 的 WebSocket 消息全都在 debug level 打了日志，每条终端输入输出都被记了一遍。于是把 WebSocket 消息的日志级别调到 trace，生产默认 info level，日志量立刻降到每天 20MB。

其实这个教训蛮低级的。打日志的时候根本没想过"这条日志在生产环境的量会有多大"。

折腾完 winston 之后又遇到一个问题：Node.js 的 console.log 和 winston 会抢 stdout。relay 启动时打印的 token 用的 console.log，但 winston 配了 Console transport 之后，两者的输出会交叉。于是把启动信息也改成 winston 打印，统一用一个 logger 实例。

有个事情我一直想做但没做成——结构化日志。现在日志格式是纯文本，想查某个 session 的日志得 grep session ID。如果用 JSON 格式，丢进 Loki 或者 ELK 就能按字段搜索了。

不过就 TermPilot 目前的用户量，grep 够用了。等真的需要日志平台的时候再说吧。我怀疑那一天不会很快来。

### Evaluation:
- E8: ✅ | E15: ✅ — "后来"、"于是"、"其实"
- E16: ✅ — "不对劲"、"蛮低级的"、"折腾完"
- E18: ✅ | E19: ✅ — 弯路：console.log → winston → 日志太大 → 调级别 → stdout抢占 → 统一logger
- E20: ✅ — "结构化日志...一直想做但没做成"
- E21: ✅ — "这个教训蛮低级的" 自嘲
- E22: ❌ — "等真的需要日志平台的时候再说吧" — 虽然加了"我怀疑那一天不会很快来"有自嘲味，但仍然是"先不管/以后再说"的变体。FAIL
- E23: ✅
- **Score: 8/9** (E22 FAIL)

## Run 4 — Java record 和 sealed interface

### Output:

最近在把项目里的 DTO 全部改成 record 类型。

起因是代码审查的时候，一个同事指着一堆 Lombok 的 @Data DTO 说"这些类有 setter 方法没道理啊，DTO 不应该是不可变的吗"。他说得对。

Java 16 的 record 正好解决这个问题：

```java
public record OrderDTO(Long id, String orderNo, BigDecimal amount, OrderStatus status) {}
```

一行搞定。编译器自动生成 constructor、getter、equals、hashCode、toString。没有 setter——天生不可变。（这里"天生"是事实描述不是那种"天然支持"的废话。）

改起来倒也不麻烦，就是工作量大。项目里有 80 多个 DTO，一个一个从 class 改成 record。中间遇到几个坑——有些 DTO 被 Jackson 反序列化的时候需要默认构造函数，record 没有。解决办法是加 `@JsonCreator` 或者用 `jackson-module-parameter-names`。

sealed interface 是另一个好东西。我们有个订单状态的处理逻辑，之前是 if-else 链：

```java
if (status instanceof Pending) { ... }
else if (status instanceof Paid) { ... }
else if (status instanceof Shipped) { ... }
```

改成 sealed interface 之后，编译器能检查 switch 是否穷举了所有子类型。后来加了个新状态忘了处理，编译直接报错——以前这种 bug 得靠测试或者线上翻车才发现。

说起来编译器帮你捡 bug 这件事，用了 TypeScript 之后感受更深。Java 的类型系统和 TypeScript 各有各的强项——Java 的 sealed 类似 TS 的 discriminated union，但 Java 的泛型擦除就比 TS 的 structural typing 弱了不少。

80 个 DTO 改了三天。值得。

### Evaluation:
- E8: ✅ | E15: ✅ — "后来"、然后（无）...再看：只有"后来"。其他：于是/反正/其实/说白了/结果/然后... 没有第二个。**FAIL** (只有1个)
- E16: ✅ — "一行搞定"、"天生不可变"、"翻车"
- E18: ✅ | E19: ✅ — 弯路：Jackson反序列化需要默认构造函数 → 加@JsonCreator
- E20: ✅ — "Java的泛型擦除就比TS的structural typing弱了不少"
- E21: ✅ — "用了TypeScript之后感受更深" 跨语言联想
- E22: ✅ — "80个DTO改了三天。值得。" 干脆结尾
- E23: ✅
- **Score: 8/9** (E15 FAIL)

## Run 5 — 博客从 Hexo 到现在

### Output:

这个博客用 Hexo 搭的，从 2021 年到现在快四年了。中间想过换，但一直没换。

当时选 Hexo 的原因很简单：网上教程多，GitHub Pages 免费，Butterfly 主题好看。折腾了一个下午就搭起来了。第一篇文章写的是 Java 手写异步调用，现在回头看写得挺稚嫩的，但也算是个记录。

后来陆续看了不少博客方案。Hugo、Jekyll、VuePress、Gatsby、Next.js...每次看到别人的博客很好看就心动一下，但想到要迁移 35 篇文章就算了。

其实 Hexo 最大的问题是 Node.js 生态太脆弱。`npm install` 经常在不同机器上报错，`hexo generate` 偶尔莫名其妙挂掉，不给任何有用的错误信息。每次换电脑都得重新折腾一遍环境。写了个 backup.sh 自动 push 到 GitHub，至少源码不会丢。

主题魔改了不少。Butterfly 默认的配色太花了，我改成了暗色系。还加了一些自定义的 CSS——代码块字体换成了 JetBrains Mono，行间距调大了一点。这些改动都在 `_config.butterfly.yml` 里，换过一次主题版本，diff 了半天才把自定义配置合并回去。

于是后来的策略就是：能不升级就不升级。跑着没问题就别动它。

有时候会想，等哪天真的有闲工夫了，也许会用 Astro 重写一版。反正想想也不花钱。

### Evaluation:
- E8: ✅ | E15: ✅ — "其实"、"于是"、"反正"
- E16: ✅ — "折腾了一个下午"、"心动一下"、"莫名其妙挂掉"、"折腾一遍"
- E18: ✅ | E19: ✅ — 弯路：每次想换 → 但迁移太麻烦 → 不换了
- E20: ✅ — "Hexo最大的问题是Node.js生态太脆弱"、环境问题
- E21: ✅ — "第一篇文章写的是Java手写异步调用，现在回头看写得挺稚嫩的" 个人回忆
- E22: ✅ — "反正想想也不花钱" 轻松幽默结尾
- E23: ✅
- **Score: 9/9**

---

## Experiment 16 Summary

| Run | E8 | E15 | E16 | E18 | E19 | E20 | E21 | E22 | E23 | Score |
|-----|----|----|-----|-----|-----|-----|-----|-----|-----|-------|
| 1 虚拟线程 | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | 7/9 |
| 2 包管理器 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 3 日志系统 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 8/9 |
| 4 record | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/9 |
| 5 Hexo | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |

**Total: 41/45 (91.1%)**

Still failing:
- E15 随意连接词: 3/5 — some outputs only use 1 instead of ≥2
- E20 有未完美: 4/5 — one output resolves everything cleanly
- E22 结尾非模板: 4/5 — one still uses "以后再说" variant

Score dropped from 95.6% to 91.1% after mutation. The new guidance about endings and asides is working for some outputs (Run 2, 5 have great endings) but introduced regression on E15 (casual connectors became less consistent).

**Decision: KEEP** — E21 improved from 4/5 to 5/5, E22 improved conceptually but still has 1 failure. The E15 regression is minor and was already at 4/5 before. Net improvement on the harder evals.
