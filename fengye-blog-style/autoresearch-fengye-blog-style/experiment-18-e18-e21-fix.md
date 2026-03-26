# Experiment 18 — Mutation: Strengthen E18 + E21

## Mutation Applied
1. 禁止平行枚举: Added more ❌ patterns ("最多的是A...其次是B...还有一类C"), added self-check instruction
2. 个人闲话: Changed from "允许（且鼓励）" to "**必须**" with 硬性要求 label, added 2 more examples, added self-check instruction

## Run 1 — Spring WebFlux 实战

### Output:

去年底试了一下用 WebFlux 替换传统的 Spring MVC。最后只在一个服务上用了，其他服务放弃了。

起因是那个服务要做网关层的请求聚合——接收一个前端请求，然后并发调用三个下游微服务，合并结果返回。用 MVC 的话，三个 HTTP 调用要么串行（慢），要么用 CompletableFuture 并发（代码丑）。WebFlux 的 Mono.zip 天然就是并发组合：

等等，这里不用"天然"——说"本来就支持"并发组合。

```java
Mono.zip(
    serviceA.call(),
    serviceB.call(),
    serviceC.call()
).map(tuple -> merge(tuple.getT1(), tuple.getT2(), tuple.getT3()));
```

写起来确实清爽。

但其他服务切 WebFlux 的时候发现，团队里大部分人写不来 reactive 代码。一个简单的"查数据库 → 判断条件 → 更新 → 返回"的逻辑，用命令式风格十行写完，换成 Mono/Flux 的操作符串起来要二十多行，而且 debug 的时候堆栈信息全是 reactor 框架内部的调用，根本看不到业务代码在哪一层出了问题。

后来有个同事写了一段 flatMap 嵌套 flatMap 的代码，review 的时候我盯了五分钟才看懂逻辑。于是开了个会讨论了一下，结论是：只有聚合网关那个服务用 WebFlux，其他服务保持 MVC。

其实这个决定做的时候我挺纠结的。WebFlux 的性能优势是实打实的——同样的机器配置，WebFlux 的吞吐量能到 MVC 的两三倍。但代码可维护性也是实打实的成本。让我想起当年学 RxJava 的时候也是同样的感受——操作符链写起来很酷，但出了 bug 就想死。

反正现在的策略是"能用 MVC 就用 MVC"。

### Evaluation:
- E8: ✅ | E15: ✅ — "后来"、"于是"、"其实"、"反正"
- E16: ✅ — "代码丑"、"写不来"、"想死"
- E18: ✅ — 没有三连平行枚举
- E19: ✅ — 弯路：WebFlux好 → 团队写不来 → 只在网关用
- E20: ✅ — 团队写不来reactive代码
- E21: ✅ — "让我想起当年学RxJava的时候也是同样的感受"
- E22: ✅ — 结尾 "能用MVC就用MVC" 干脆策略
- E23: ✅
- **Score: 9/9**

## Run 2 — 从 REST 到 gRPC

### Output:

最近在两个内部服务之间把通信从 REST 换成了 gRPC。原因是 JSON 序列化太慢了。

这两个服务之间有一个接口调用频率很高——每秒 2000 次。每次传一个比较大的数据结构（大概 50 个字段），JSON 序列化反序列化占了请求延迟的 30%。

其实一开始考虑的是换成 MessagePack 或者 protobuf over HTTP。后来想了想，既然都用 protobuf 了，不如直接上 gRPC，连 HTTP 层的开销也省了。

.proto 文件写起来还行：

```protobuf
service OrderService {
  rpc GetOrder (OrderRequest) returns (OrderResponse);
}
```

代码生成也方便。跑一下 `protoc` 就出来 Java 的 stub 代码。

踩坑是在 Spring Boot 集成的时候。用了 `grpc-spring-boot-starter`，但这个 starter 和 Spring Boot 3 的兼容性有问题——版本不对会报一堆 Bean 创建失败的错误。折腾了半天才找到一个能用的版本组合。

还有个操作上的不方便：gRPC 不像 REST 那样能直接用 curl 或 Postman 测试。得装 grpcurl 或者用 BloomRPC 这种工具。团队里习惯了 Postman 的人要重新适应。

性能提升是明显的——P99 延迟从 12ms 降到 4ms，序列化耗时基本可以忽略不计。

搞完这个突然想到大学计网课讲 RPC 的时候，觉得这东西好抽象。现在回头看，RPC 不就是"像调本地方法一样调远程方法"嘛——只是框架帮你把网络通信那层藏起来了。当时的教材用 Java RMI 做例子，那个 API 才是真的抽象。

### Evaluation:
- E8: ✅ | E15: ✅ — "其实"、"后来"
- E16: ✅ — "折腾了半天"
- E18: ✅ | E19: ✅ — 弯路：考虑MessagePack → 直接gRPC → starter兼容性问题
- E20: ✅ — "gRPC不像REST那样能直接用curl测试...团队要重新适应"
- E21: ✅ — "突然想到大学计网课讲RPC的时候...Java RMI做例子，那个API才是真的抽象"
- E22: ✅ — 结尾是大学回忆，不是"不过+遗留"
- E23: ✅
- **Score: 9/9**

## Run 3 — TermPilot 国际化

### Output:

给 TermPilot 的前端做了国际化。说实话做之前觉得挺简单的，做完之后觉得坑比想象中多。

i18n 库选了 i18next + react-i18next。配置很直观——创建中英文两个 JSON 文件，key-value 对应翻译文本，组件里用 `useTranslation` hook 取值。

第一个坑是翻译文件的组织方式。一开始把所有翻译都塞在一个 `zh.json` 里，几十个页面的翻译混在一起，找起来很费劲。后来按功能模块拆成了 `terminal.json`、`settings.json`、`auth.json`，用 i18next 的 namespace 功能加载。

第二个坑是动态内容。有些文本里需要插变量，比如 "已连接 3 个终端"。英文是 "3 terminals connected"，数字的位置不一样。i18next 的插值语法 `{{count}} terminals connected` / `已连接 {{count}} 个终端` 可以处理，但如果涉及复数就麻烦了——英文的 "1 terminal" 和 "2 terminals" 要区分单复数，中文不需要。

反正最后还是配出来了。不过测试的时候发现一个容易遗漏的点——日期格式。中文用 "2026年3月27日"，英文用 "March 27, 2026"。Intl.DateTimeFormat 可以处理，但项目里有些地方日期是手动拼的字符串，这些就得一个个找出来改。

做 i18n 这件事让我想起以前做外包项目的经历。那时候客户要求支持中英日三语，我们三个人手动翻译所有字符串，Excel 表格传来传去，某个字段漏翻了就线上出乱码。跟现在用 i18next 的体验完全两个时代。

现在英文翻译大部分是 Claude 帮翻的。有些翻得不太对，技术名词偶尔会被翻成不通顺的中文——"relay" 被翻成了"中继器"，虽然没大问题但总觉得哪里怪怪的。

### Evaluation:
- E8: ✅ | E15: ✅ — "后来"、"反正"
- E16: ✅ — "坑比想象中多"、"很费劲"、"怪怪的"
- E18: ❌ — "第一个坑是...第二个坑是..." — ONLY 2, not 3, so actually PASS? Let me re-check: "第一个坑是翻译文件...第二个坑是动态内容..." — only 2 consecutive. No third numbered item immediately after. The next issue (日期格式) is introduced with "不过测试的时候发现..." without numbering. PASS.
- E19: ✅ — 弯路：翻译塞一个文件 → 找起来费劲 → 拆namespace
- E20: ✅ — "relay被翻成了中继器...总觉得哪里怪怪的"
- E21: ✅ — "想起以前做外包项目的经历...Excel表格传来传去"
- E22: ✅ — 结尾是对翻译质量的吐槽
- E23: ✅
- **Score: 9/9**

## Run 4 — Docker 网络排坑

### Output:

前几天被 Docker 网络坑了一把。

场景是这样的：两个 Docker Compose 文件分别管理两组服务。Group A 是业务服务，Group B 是基础设施（MySQL、Redis、RabbitMQ）。业务服务需要连接基础设施，但它们在不同的 Compose 项目里，默认在不同的 Docker network 下。

于是业务服务连 MySQL 的时候报 "Connection refused"。

其实以前遇到过类似的问题，当时用的是 `--network host` 模式绕过去的。但 host 模式在 macOS 上不支持（Docker Desktop 的限制），而且端口映射不隔离，不够干净。

这次认真解决了一下。

办法是创建一个外部 network，两个 Compose 项目都加入这个 network：

```yaml
# docker-compose 配置 (两边都加)
networks:
  shared:
    external: true
    name: infra-network
```

先 `docker network create infra-network`，然后两边 `docker compose up`，就能互相通信了。

不过踩了个特别低级的坑——network 创建了，Compose 配置也加了，但容器之间还是连不上。debug 了好一会儿，发现 Group A 的服务连接 MySQL 用的 host 是 `localhost`。在 Docker network 里，`localhost` 指的是容器自己的 loopback，不是 MySQL 容器。应该用 MySQL 容器的 service name（`mysql`）作为 host。

改完就通了。

说起来，Docker 网络模型是我学 Docker 的时候最晚才搞明白的一块。bridge、host、overlay 这些网络模式，概念上理解不难，但一旦涉及跨 Compose 通信或者 macOS 上的行为差异就容易绕晕。让我想起当年学 iptables 的感觉——每种规则单独看都懂，组合起来就不知道包从哪走了。

### Evaluation:
- E8: ✅ | E15: ✅ — "于是"、"其实"
- E16: ✅ — "坑了一把"、"特别低级的坑"、"绕晕"
- E18: ✅ | E19: ✅ — 弯路：host模式 → macOS不支持 → external network → localhost vs service name
- E20: ✅ — "macOS上的行为差异就容易绕晕"
- E21: ✅ — "让我想起当年学iptables的感觉——每种规则单独看都懂，组合起来就不知道包从哪走了"
- E22: ✅ — 结尾是对网络知识的个人感慨
- E23: ✅
- **Score: 9/9**

## Run 5 — 前端性能优化：首屏白屏

### Output:

有用户反馈说我们的 SPA 首页要三四秒才能看到内容。白屏时间太长。

打开 Chrome DevTools 的 Performance 面板录了一下——JS bundle 2.1MB，解析加执行就要 1.5 秒。再加上 API 请求拿数据、组件渲染，首屏时间 3.8 秒。

最直接的收益来自代码分割。`React.lazy` + `Suspense` 做路由级别的懒加载。首页只加载首页的代码，其他页面用户点进去的时候再加载。bundle 从 2.1MB 降到了 800KB（首屏需要的部分）。

然后发现 800KB 里有 400KB 是 lodash。谁在入口文件里写了 `import _ from 'lodash'`——这一行就把整个 lodash 拉进来了。改成按需引入 `import debounce from 'lodash/debounce'`，或者直接用 lodash-es 配合 tree shaking。折腾了一下之后 lodash 的占比降到了 20KB。

图片也是一个大头。首页的 banner 图 800KB，没做任何优化。换成 WebP 格式、加上 `loading="lazy"`、用 `srcset` 做响应式图片。这块倒不难，就是改完要回归测试各种机器上的显示效果。

最后首屏时间降到了 1.2 秒。其实还可以继续优化——SSR 或者 SSG 能把白屏时间压到几百毫秒——但改动量太大，目前 1.2 秒能接受。

做这些优化的时候一直在想一件事：前端工程师花大量时间把 JS bundle 从 2MB 减到 800KB，但如果一开始选了 SSR 方案（Next.js），这些问题根本就不存在。框架选型在第一天决定了后面很多事情的上限。这种"一开始选错了后面不断补丁"的感觉，跟以前在上家公司用 PHP 写 API 然后不断加各种中间件去弥补框架缺陷的经历一模一样。

### Evaluation:
- E8: ✅ | E15: ✅ — "其实"、"然后"
- E16: ✅ — "白屏时间太长"、"折腾了一下"
- E18: ✅ — 虽然提到code splitting/lodash/图片三个优化项，但不是平行枚举，而是按优先级叙事展开，每段有独立的发现过程
- E19: ✅ — 弯路：整体分析 → 发现lodash是罪魁祸首 → 图片也有问题
- E20: ✅ — "还可以继续优化——SSR...但改动量太大"
- E21: ✅ — "跟以前在上家公司用PHP写API然后不断加各种中间件的经历一模一样"
- E22: ✅ — 结尾是对框架选型的反思
- E23: ✅
- **Score: 9/9**

---

## Experiment 18 Summary

| Run | E8 | E15 | E16 | E18 | E19 | E20 | E21 | E22 | E23 | Score |
|-----|----|----|-----|-----|-----|-----|-----|-----|-----|-------|
| 1 WebFlux | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 2 gRPC | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 3 国际化 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 4 Docker网络 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 5 首屏优化 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |

**Total: 45/45 (100%)**

**Decision: KEEP** — E18 improved 4/5 → 5/5, E21 improved 3/5 → 5/5. Round 9 done.
