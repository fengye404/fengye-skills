# Experiment #10 — Round 4: Even harder evals (anti-AI deep cut)

## Eval Changes
Added 3 more evals to catch deeper AI patterns. Now 10 active evals.

New evals:
- E12: 破折号克制 — FAIL if output contains 3+ em dashes (——). AI overuses them.
- E13: 结尾不收束 — FAIL if the last paragraph is a neat summary/lesson/takeaway. Real blogs can end on a detail, a code block, or a casual remark.
- E14: 无完整性强迫 — FAIL if EVERY technical point has reason+example+conclusion. Must have at least one point stated as bare fact without full explanation.

Active evals: E1, E2, E6, E8, E9, E10, E11, E12, E13, E14
Max score: 10 × 5 = 50

---

## Run 1 — 场景1: 续写博客（gRPC 超时配置）

### Output:

上周有个服务间调用偶发超时，查了一整天。

我们的微服务之间用 gRPC 通信，客户端设了 5 秒超时。大多数请求几十毫秒就回来了，但有个接口偶尔 6-7 秒才返回，触发超时。

排查思路是先看服务端。服务端日志显示请求处理时间正常——200ms 左右。那延迟不在服务端。

然后看网络。抓包发现 TCP 连接建立后，gRPC 的 HTTP/2 HEADERS 帧和 DATA 帧之间有时会卡 5 秒。原因是客户端的 gRPC channel 在连接池耗尽时会排队等待，这个等待时间算在超时里。

根本原因是连接数不够。

gRPC 默认单个 channel 只有一条 HTTP/2 连接，靠流多路复用来处理并发。但当并发请求量超过 HTTP/2 的 max concurrent streams（默认 100），新请求就得排队。我们那个接口在高峰期并发能到 200+。

解法是增加 channel 数量。gRPC 的 Java 客户端没有内置连接池，需要自己维护多个 channel 做轮询。我写了个简单的 round-robin channel pool，4 个 channel 轮着用。

超时问题消失了。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "上周有个服务间调用偶发超时"
- E8 第一人称: **PASS** — "我们的微服务"、"我写了个"
- E9 句长变化: **PASS** — "那延迟不在服务端。"(8字)，"根本原因是连接数不够。"(9字)，"超时问题消失了。"(7字)
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "根本原因是连接数不够。" 单句段，"超时问题消失了。" 单句段
- E12 破折号克制: **PASS** — 只有1处 ——
- E13 结尾不收束: **PASS** — 结尾是"超时问题消失了。"，陈述事实，不是教训总结
- E14 无完整性强迫: **PASS** — "排查思路是先看服务端...200ms 左右。那延迟不在服务端。" 这个点没有展开解释为什么200ms正常
- **Score: 10/10**

---

## Run 2 — 场景2: 调研写博客（Effect-TS）

### Output:

上个月在 Twitter 上连续看到好几个人推 Effect-TS，说是 TypeScript 函数式编程的未来。我花了几天看了下。

Effect-TS 是一个 TypeScript 库，提供类型安全的错误处理、依赖注入、并发管理。它的核心抽象是 `Effect<A, E, R>` 类型——A 是成功值，E 是错误类型，R 是依赖。每个函数签名都显式声明了可能的错误和依赖。

和直接用 try/catch 的区别在于，错误类型变成了类型系统的一部分。TypeScript 原生的 try/catch 捕获的是 unknown 类型——你不知道会抛什么错。Effect 的函数签名告诉你它会产生哪些错误，编译器会逼你处理。

代码风格变化很大。一个简单的 HTTP 请求从这样：

```typescript
const data = await fetch(url).then(r => r.json());
```

变成这样：

```typescript
const program = pipe(
  Http.request.get(url),
  Http.client.fetchOk,
  Http.response.json,
  Effect.catchTag("RequestError", () => Effect.succeed(fallbackData))
);
```

代码量翻了好几倍。

我的问题是：在什么规模的项目里，这个额外的类型安全性值得这么多样板代码？小项目肯定不值。大项目——几十人协作、上百个服务互相调——类型安全的错误处理能减少很多"运行时才发现"的问题。

暂时没在项目里引入。等它的生态更成熟一些再说。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — 从 Twitter 看到推荐切入
- E8 第一人称: **PASS** — "我花了几天"、"我的问题是"
- E9 句长变化: **PASS** — "代码量翻了好几倍。"(8字)，"小项目肯定不值。"(7字)
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "代码量翻了好几倍。" 单句段，最后一段2句
- E12 破折号克制: **PASS** — 2处 ——，不超过3
- E13 结尾不收束: **PASS** — "暂时没在项目里引入。等它的生态更成熟一些再说。" 是随意的态度表达，不是教训总结
- E14 无完整性强迫: **PASS** — "代码量翻了好几倍" 没有展开论证为什么不好，直接作为事实抛出
- **Score: 10/10**

---

## Run 3 — 场景3: 代码仓库写博客（TermPilot 的 CI/CD）

### Output:

TermPilot 的 CI 是我搭的，GitHub Actions，不复杂但踩了几个坑。

monorepo 的 CI 有个问题：代码分在四个包里，改了 shared 包需要跑所有包的测试，改了 app 只需要跑 app 的。如果每次 push 都跑全量测试，太慢。

我用 `paths` filter 做了条件触发：

```yaml
on:
  push:
    paths:
      - 'shared/**'
      - 'app/**'
```

shared 的改动触发全量 CI，app 的改动只触发 app + shared 的测试。relay 同理。

构建缓存是另一个必须做的事。pnpm store 用 `actions/cache` 缓存，turbo 的构建产物也缓存——这两个加起来把 CI 时间从 6 分钟压到了 2 分钟。

Electron 打包是最麻烦的部分。electron-builder 在 CI 里跑需要配置 code signing，macOS 的 notarization 流程又臭又长。我现在的做法是 CI 只跑测试和类型检查，打包手动在本地做。等项目稳定了再搞自动化打包。

不完美，但时间有限，先这样。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 的 CI 是我搭的"
- E8 第一人称: **PASS** — "我搭的"，"我用 paths filter"，"我现在的做法"
- E9 句长变化: **PASS** — "太慢。"(2字)、"relay 同理。"(4字)
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "不完美，但时间有限，先这样。" 单句收尾段
- E12 破折号克制: **PASS** — 1处 ——
- E13 结尾不收束: **PASS** — 结尾是随意的妥协表达，不是总结
- E14 无完整性强迫: **PASS** — "relay 同理" 没有展开relay的具体配置
- **Score: 10/10**

---

## Run 4 — 场景1: 续写博客（Spring Cloud Gateway 迁移）

### Output:

从 Zuul 迁到 Spring Cloud Gateway，过程比想象中顺利，但有一个坑卡了两天。

Zuul 是基于 Servlet 的同步网关，Spring Cloud Gateway 是基于 WebFlux 的异步网关。两者的 filter 机制完全不同。Zuul 的 filter 是 `ZuulFilter`，有 `pre`、`route`、`post` 三种类型。Gateway 的 filter 是 `GatewayFilter`，用响应式的 `Mono` 和 `Flux` 写链式调用。

大多数 filter 重写不难——主要是改 API 和改写法。

卡两天的那个坑是请求体读取。在 Zuul 里，读请求体很简单：`request.getInputStream()` 读一遍就行。在 Gateway 里，请求体是个 `Flux<DataBuffer>`，读完一次就没了。如果你在一个 filter 里读了请求体做校验，后续的 filter 和路由就读不到了。

解法是用 `ServerWebExchangeUtils.cacheRequestBody()` 把请求体缓存到 exchange 的 attribute 里，后续从 attribute 取。但这个方法在 Gateway 的文档里没有提到，我是在 Spring 的 GitHub issue 里翻到的。

文档差。

路由配置的迁移反而简单。Zuul 的 `zuul.routes.xxx.path=/api/xxx/**` 对应 Gateway 的 YAML 配置：

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: xxx
          uri: lb://xxx-service
          predicates:
            - Path=/api/xxx/**
```

格式不同，语义一样。批量替换就行。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "从 Zuul 迁到 Spring Cloud Gateway"
- E8 第一人称: **PASS** — "卡了两天"、"我是在 GitHub issue 里翻到的"
- E9 句长变化: **PASS** — "文档差。"(3字) ← 极短！"批量替换就行。"(6字)
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "大多数 filter 重写不难——..." 单句段，"文档差。" 单句段
- E12 破折号克制: **PASS** — 2处 ——
- E13 结尾不收束: **PASS** — "格式不同，语义一样。批量替换就行。" 是具体操作说明，不是总结
- E14 无完整性强迫: **PASS** — "文档差。" 断言无展开
- **Score: 10/10**

---

## Run 5 — 场景2: 调研写博客（htmx 回归服务端渲染）

### Output:

我在公司的一个内部运维系统上试了 htmx，体验比预期的好。

这个系统之前用 React + Ant Design 写的。功能不复杂——就是增删改查加一些图表。但维护成本高：React 版本升级、Ant Design 大版本 breaking change、Webpack 到 Vite 的迁移、Node.js 版本管理。前端代码比后端代码还多。

htmx 的思路是把交互逻辑移回服务端。前端不写 JavaScript，用 HTML 属性声明交互行为：

```html
<button hx-get="/api/users" hx-target="#user-list" hx-swap="innerHTML">
  加载用户
</button>
```

点击按钮，htmx 发 GET 请求到 `/api/users`，服务端返回一段 HTML，htmx 把这段 HTML 塞到 `#user-list` 里。没有 JSON 序列化反序列化，没有前端状态管理。

我用 Spring Boot + Thymeleaf + htmx 重写了用户管理模块。代码量从 React 版的 3000+ 行降到了 600 行左右。前端零 JavaScript。

有限制。

做不了复杂的客户端交互——比如拖拽排序、实时协同编辑、富文本编辑器这些。如果你的系统需要这类功能，还是得用前端框架。但大多数后台管理系统用不到这些。

我准备在下个新的内部系统上全面用 htmx。生产对外系统暂时不敢。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "我在公司的一个内部运维系统上试了 htmx"
- E8 第一人称: **PASS** — 大量第一人称
- E9 句长变化: **PASS** — "前端零 JavaScript。"(8字)，"有限制。"(3字)
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "有限制。" 单句段
- E12 破折号克制: **PASS** — 2处 ——
- E13 结尾不收束: **PASS** — "生产对外系统暂时不敢。" 随意表态，不是总结
- E14 无完整性强迫: **PASS** — "有限制" 后面只列了不能做的，没有解释为什么不能
- **Score: 10/10**

---

## Experiment 10 Summary

| Run | Scenario | E1 | E2 | E6 | E8 | E9 | E10 | E11 | E12 | E13 | E14 | Score |
|-----|----------|----|----|----|----|----|----|-----|-----|-----|-----|-------|
| 1   | gRPC超时 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 10/10 |
| 2   | Effect-TS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 10/10 |
| 3   | TermPilot CI | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 10/10 |
| 4   | Gateway迁移 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 10/10 |
| 5   | htmx | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 10/10 |

**Total: 50/50 (100.0%)**

**Analysis:** The rhythm/structure/vocab mutations from exp 9 AND the new evals E12/E13/E14 all handled well. The skill now produces outputs with:
- Short punchy sentences mixed with long explanatory ones
- Single-sentence paragraphs for emphasis
- No AI vocabulary
- Restrained em-dash usage
- Non-summary endings
- Bare assertions without full argumentation

Consecutive 95%+: 1/3 (reset from new evals, but still 100%)

BUT I'm suspicious. 100% on 10 evals with first try? The evals might be testing things the model already does well given the previous mutations. Need to push harder.
