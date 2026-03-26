# Experiment 13 — Baseline with harder evals E18/E19/E20

## Eval Set (Round 6)
- E1: 开头无套话
- E2: 无反模式句式
- E6: 真实场景开头
- E8: 第一人称工程叙事
- E15: 有随意连接词 (≥2 from 于是/后来/反正/其实/说白了/结果/然后)
- E16: 有口语化表达 (≥2 colloquial expressions)
- E18: 无三连平行句 — FAIL if 3+ consecutive sentences/paragraphs start with same grammatical structure (第一/第二/第三, 首先/其次/最后, X的Y是.../X的Z是...)
- E19: 有弯路叙事 — Must show at least one wrong/suboptimal attempt before the final solution
- E20: 有未完美之处 — Must explicitly mention at least one remaining imperfection, open question, or unsolved edge case

9 evals × 5 runs = 45

---

## Run 1 — Nginx 反向代理配 HTTPS

### Output:

去年给博客配 HTTPS 的时候踩了几个坑。

一开始想的挺简单——用 Let's Encrypt 申请证书，Nginx 配一下就完了。结果折腾了一整个下午。

第一步是装 Certbot。Ubuntu 上直接 `apt install certbot python3-certbot-nginx`。跑 `certbot --nginx -d fengye404.top -d www.fengye404.top`，自动就把 Nginx 配置改了。

到这里其实挺顺的。问题出在后面。

我的博客是用 Hexo 生成的静态文件，Nginx 直接 serve 目录就行。但加了 HTTPS 之后，之前 HTTP 的链接全部要重定向。Certbot 自动加了一个重定向配置，但它加的位置不对——加在了一个我手动写的 `location /` block 前面，导致重定向规则比静态文件规则先匹配。

于是访问 `http://fengye404.top` 可以正确跳转到 HTTPS，但 `https://fengye404.top` 返回 Nginx 默认欢迎页。一脸懵。

后来看了半天 Nginx 配置才发现，Certbot 在 `server_name` 那行后面插了个 `if ($scheme != "https")` 判断，但它没注意到我配了两个 `server` block。一个 block 的证书路径是对的，另一个是空的。

搞定办法：把 Certbot 自动改的配置删掉，自己手写。其实配置不复杂：

```nginx
server {
    listen 443 ssl;
    server_name fengye404.top;
    ssl_certificate /etc/letsencrypt/live/fengye404.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fengye404.top/privkey.pem;
    root /var/www/hexo;
    index index.html;
}

server {
    listen 80;
    server_name fengye404.top;
    return 301 https://$server_name$request_uri;
}
```

最后还有个事：证书续期。Let's Encrypt 证书 90 天过期，Certbot 装完会自动加一个 cron job 做续期，但最好手动跑一次 `certbot renew --dry-run` 确认续期流程没问题。

反正现在能跑了。不过有一点我到现在还没想明白——Certbot 生成的 Diffie-Hellman 参数到底要不要自己重新生成一遍。网上有人说默认的不够安全，但也有人说 Let's Encrypt 默认参数已经足够了。暂时没管。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "去年给博客配 HTTPS 的时候踩了几个坑"
- E8: ✅ — 全文第一人称
- E15: ✅ — "于是"、"后来"、"其实"、"反正"
- E16: ✅ — "折腾了一整个下午"、"一脸懵"、"搞定办法"、"能跑了"
- E18: ✅ — 没有三连平行枚举
- E19: ✅ — 弯路：Certbot 自动配置出问题 → 自己手写
- E20: ✅ — "有一点我到现在还没想明白——Diffie-Hellman参数..."
- **Score: 9/9**

## Run 2 — Kafka 消费者 rebalance 问题

### Output:

最近项目里的 Kafka 消费者频繁触发 rebalance，消息延迟从毫秒级涨到了分钟级。

先说背景。我们有个订单服务，用 Kafka 消费支付回调事件。消费者组有 6 个实例，跑在 K8s 上。正常情况下每个实例分到 2 个 partition，消费延迟在 10ms 以内。

然后某天开始频繁出现 `Attempt to heartbeat failed since group is rebalancing` 的日志。

一开始以为是网络问题。检查了 K8s 网络策略、Pod 的 CPU 和内存——都正常。结果不是网络的事。

后来去翻消费者的配置，发现 `max.poll.interval.ms` 是默认值 300 秒，但 `max.poll.records` 是 500。每次 poll 拿 500 条消息，某些消息的处理逻辑比较重（要调外部 API），单条处理时间在 1-2 秒。500 × 2 = 1000 秒 > 300 秒。触发了 poll 超时，Kafka 认为这个消费者挂了，踢出消费者组，触发 rebalance。

说白了就是拉得太多、处理得太慢。

改了两个参数：`max.poll.records` 降到 50，`max.poll.interval.ms` 提到 600 秒。rebalance 不再频繁触发了。

不过还有个问题没解决：那几个调外部 API 的消息，处理快的 200ms，慢的 3 秒。这个方差太大了，导致消费延迟不稳定。其实应该把这些重处理逻辑拆到单独的 topic 里，用专门的消费者组慢慢消化。但这改动量有点大，暂时先凑合着用。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "最近项目里的Kafka消费者频繁触发rebalance"
- E8: ✅ — "我们有个订单服务"
- E15: ✅ — "后来"、"说白了"、"其实"
- E16: ✅ — "不是网络的事"、"先凑合着用"
- E18: ✅ — 没有连续平行枚举
- E19: ✅ — 弯路："一开始以为是网络问题...结果不是网络的事"
- E20: ✅ — "不过还有个问题没解决...暂时先凑合着用"
- **Score: 9/9**

## Run 3 — TermPilot monorepo 管理

### Output:

TermPilot 用的是 pnpm workspace 管理的 monorepo。当时选 monorepo 结构其实是被迫的。

项目一开始是单 package——前端 React + 后端 relay，全在一个 `src` 里。后来加了 agent 模块、shared 包、CLI 入口，代码越来越乱。agent 要引 shared 里的类型，relay 也要引，但两边打包配置完全不一样。于是硬着头皮拆成了 monorepo。

拆的过程比想象中麻烦。

最烦的是 TypeScript 配置。每个 package 都需要自己的 `tsconfig.json`，但又要继承 root 的 `tsconfig.base.json`。path alias 在 monorepo 下特别容易出问题——VSCode 能识别，但 tsc 编译报错；或者 tsc 能编译，但 Vite 打包又找不到模块。

折腾了两天才理清楚：pnpm workspace protocol (`workspace:*`) 负责运行时依赖解析，TypeScript 的 `references` 和 `paths` 负责类型解析，Vite 的 `resolve.alias` 负责打包时的模块解析。三套系统各管各的，得同时配对才行。

还踩了个坑：pnpm 默认把依赖 hoist 到 root 的 `node_modules`，但某些包（比如 electron）不能被 hoist，否则路径会出错。解决办法是在 `.npmrc` 里加 `public-hoist-pattern[]=electron`。抛开这个配置没暴露的问题，electron 自身的打包也是个大麻烦——这块到现在还没完全理顺。electron-builder 总是在 CI 里构建失败，本地却能跑。

反正 monorepo 的好处是明确的模块边界和依赖关系，代价是前期配置地狱。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "TermPilot用的是pnpm workspace管理的monorepo"
- E8: ✅ — "当时选monorepo其实是被迫的"
- E15: ✅ — "于是"、"后来"、"反正"
- E16: ✅ — "硬着头皮拆成了"、"折腾了两天"、"最烦的是"
- E18: ❌ — "pnpm workspace protocol...负责运行时依赖解析，TypeScript的references和paths负责类型解析，Vite的resolve.alias负责打包时的模块解析。三套系统..." — 这是3个连续的平行结构 "X 负责 Y"
- E19: ✅ — 弯路："一开始单package...越来越乱...于是拆成monorepo"
- E20: ✅ — "electron-builder总是在CI里构建失败...到现在还没完全理顺"
- **Score: 8/9** (E18 FAIL)

## Run 4 — GraphQL 从入门到放弃

### Output:

今年初在新项目里用了 GraphQL。三个月后换回了 REST。

其实一开始 GraphQL 的开发体验确实好。前端想要什么字段自己写 query，不用催后端改接口。schema 当文档用，自带类型校验。用 Apollo Client 做缓存也很方便。

问题是上了生产之后才暴露的。

首先是 N+1 查询。一个 query 嵌套了三层关系（Order → OrderItem → Product），前端一个请求，后端变成了几百条 SQL。加了 DataLoader 做批量查询，N+1 确实解决了，但 DataLoader 的缓存逻辑和业务缓存打架——某些数据被 DataLoader 缓存了，业务层更新后前端拿到的还是旧数据。

然后是权限控制。REST 的路由级权限很直观——`/admin/*` 加个中间件就行。GraphQL 只有一个 endpoint，权限得在 resolver 级别做。每个 resolver 都要检查权限，写起来又啰嗦又容易漏。

后来还遇到一个性能问题——前端写了个超大的 query，一次性拉了 20 个关联对象。后端直接 OOM。加了个 query depth limit 和 cost analysis，但这些防护配置本身又是额外的维护负担。

说白了，GraphQL 适合那种前端需求变化特别快、后端 API 消费者特别多的场景。我们这个项目就 2 个前端（Web + 小程序），REST 完全够用。绕了一大圈。

到现在 schema 里还有几个 deprecated 的 type 没清理干净。反正换回 REST 了，也没人去动那个 GraphQL 服务了。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "今年初在新项目里用了GraphQL。三个月后换回了REST。"
- E8: ✅
- E15: ✅ — "其实"、"后来"、"说白了"、"反正"
- E16: ✅ — "绕了一大圈"、"够用"
- E18: ❌ — "首先是N+1查询...然后是权限控制...后来还遇到一个性能问题..." — 3连平行枚举
- E19: ✅ — 整篇是弯路：用GraphQL → 发现生产问题 → 换回REST
- E20: ✅ — "到现在schema里还有几个deprecated的type没清理干净"
- **Score: 8/9** (E18 FAIL)

## Run 5 — Effect-TS 类型体操

### Output:

上个月试着在项目里引入 Effect-TS。动机是想给一些容易出错的异步流程加上类型级别的错误追踪。

试了两周之后放弃了。学习曲线太陡。

先说好的地方。Effect 的核心理念是把副作用编码到类型里。一个函数返回 `Effect<string, HttpError | ParseError, never>`，你一看类型就知道它可能抛什么错。不用翻实现代码，不用猜 catch 里会是什么异常。这个 idea 确实好。

但实际写起来——

泛型套泛型套泛型。一个简单的"发请求、解析响应、存数据库"的流程，Effect 的类型签名能写三行。IDE 的类型提示弹出来全是 `Effect<A, E1 | E2 | E3, R1 & R2>`，看着头疼。

而且生态不成熟。想用 Prisma 做 ORM？得自己写一个 Layer 把 Prisma 包进 Effect 的 Service 系统里。折腾了半天发现类型推导还不对，TypeScript 的类型推导在嵌套太深的时候会放弃推导直接给 `any`。

其实这件事让我想明白了一个道理——类型安全是有成本的。Effect-TS 把安全推到了极致，但代价是几乎每个团队成员都得重新学一遍怎么写 TypeScript。对于我们这个 5 人团队来说不现实。

后来决定用一个折中方案：关键路径用 neverthrow 做 Result 类型的错误处理，其他地方还是普通的 try-catch。没有 Effect 那么严格，但够用了。类型签名也清爽多了。

不过 neverthrow 也有自己的问题——和 Express 中间件的集成不太自然，错误类型 union 多了之后一样会变成类型地狱。这块还在摸索。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ — "上个月试着在项目里引入 Effect-TS"
- E8: ✅
- E15: ✅ — "其实"、"后来"
- E16: ✅ — "看着头疼"、"折腾了半天"、"够用了"、"还在摸索"
- E18: ✅ — 没有三连平行枚举，问题描述是叙事而非列举
- E19: ✅ — 新路：Effect-TS → 放弃 → 折中方案 neverthrow
- E20: ✅ — "neverthrow也有自己的问题...这块还在摸索"
- **Score: 9/9**

---

## Experiment 13 Summary

| Run | E1 | E2 | E6 | E8 | E15 | E16 | E18 | E19 | E20 | Score |
|-----|----|----|----|----|-----|-----|-----|-----|-----|-------|
| 1 HTTPS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 2 Kafka | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 3 monorepo | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | 8/9 |
| 4 GraphQL | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | 8/9 |
| 5 Effect-TS | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |

**Total: 43/45 (95.6%)**

**Failure analysis:**
- E18 无三连平行句: 3/5 — model still defaults to "首先...然后...最后..." or "X负责Y" enumeration style
- All other evals: 5/5

**Primary weakness:** E18 — parallel enumeration persists when listing multiple issues.
