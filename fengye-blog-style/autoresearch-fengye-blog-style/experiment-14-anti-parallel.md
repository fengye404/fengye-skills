# Experiment 14 — Mutation: Anti-parallel enumeration

## Mutation Applied
Added new section "禁止平行枚举" to the skill:
- Explicitly bans 3+ consecutive same-structure sentences
- Provides alternative strategies: expand one into narrative, merge two with casual connectors, focus on 1-2 key points
- ❌→✅ examples showing flatten enumeration into narrative

## Run 1 — K8s Pod OOMKilled 排查

### Output:

昨天有个服务的 Pod 莫名其妙重启了。`kubectl describe pod` 一看，Last State 写着 OOMKilled。

其实这个服务之前一直稳定跑了三个月，突然 OOM 有点奇怪。先看 Grafana 的内存图——过去 24 小时内存从 300MB 缓慢涨到了 512MB 的 limit，然后被 K8s 干掉了。典型的内存泄露。

先怀疑是某次上线引入的。翻了最近的提交，发现两天前有个同事加了一个定时任务，每分钟从数据库拉一批数据做缓存。问题在于这个缓存用的是 `HashMap`，只有写入没有淘汰。数据量每天涨几千条，内存就这么慢慢被吃完了。

改成 Caffeine 的 LRU 缓存，设了个 10000 条的上限。搞定。

不过后来我想了想，OOM 的时候 K8s 直接 kill 进程，没有 graceful shutdown，正在处理的请求全部丢了。于是又加了个 pre-stop hook，在被杀之前先把服务从 Service 的 endpoint 列表摘掉，等已有请求处理完再退出。

反正现在 Pod 的 memory limit 也从 512MB 提到了 768MB。多留点余量，泄露再发生的时候有更多时间排查，不至于直接崩。

不过说实话，更好的做法应该是加个内存使用率的告警，超过 70% 就通知。但我们的告警系统现在还是半残状态——这个以后再说。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅
- E15: ✅ — "其实"、"于是"、"反正"
- E16: ✅ — "莫名其妙"、"搞定"、"半残状态"
- E18: ✅ — 没有三连平行枚举，问题是叙事性展开
- E19: ✅ — 弯路：需要查提交记录才发现 HashMap 缓存无淘汰
- E20: ✅ — "告警系统现在还是半残状态——这个以后再说"
- **Score: 9/9**

## Run 2 — 前端状态管理选型 (Redux vs Zustand vs Jotai)

### Output:

新项目的状态管理库纠结了一周。最后选了 Zustand。

其实按团队经验应该直接上 Redux Toolkit——大家都会用，文档全，社区大。但我实在是写烦了。每次加一个状态要创建 slice、写 reducer、导出 action，一个简单的计数器都得写二十行。

于是试了 Zustand。五分钟就写出了一个全局 store：

```typescript
const useStore = create((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
}));
```

就这么简单。没有 Provider，没有 boilerplate。组件里直接 `const count = useStore(s => s.count)` 就能用。

Jotai 也看了。它的思路更极端——把每个状态拆成独立的 atom，完全原子化。写小组件挺爽的，但项目大了之后 atom 满天飞，找一个状态定义在哪里都费劲。折腾了一个下午试了几个页面就放弃了。

Zustand 跑了两个月了，暂时没踩什么大坑。唯一不太舒服的是 TypeScript 类型推导在嵌套 store 比较深的时候会变慢，IDE 的自动补全要等一两秒。还有中间件的类型定义也有点绕——`devtools` 和 `persist` 叠在一起的时候泛型会变得很复杂。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "我实在是写烦了"
- E15: ✅ — "其实"、"于是"
- E16: ✅ — "写烦了"、"就这么简单"、"挺爽的"、"费劲"、"折腾了一个下午"
- E18: ✅ — Redux/Zustand/Jotai 不是平行枚举，而是按尝试顺序叙事展开
- E19: ✅ — 弯路：Redux 太繁琐 → 试 Jotai failed → 最终 Zustand
- E20: ✅ — "TypeScript类型推导在嵌套store比较深的时候会变慢...中间件类型定义也有点绕"
- **Score: 9/9**

## Run 3 — TermPilot CI/CD pipeline

### Output:

TermPilot 的 CI 是用 GitHub Actions 搭的。说实话搭得比较糙。

一开始只有一个 workflow——push 到 main 就跑 lint + test + build。后来打包逻辑越来越复杂，一个 workflow 塞了 200 多行 YAML，看着头疼。于是拆成了三个：ci.yml 跑检查，release.yml 管发版，deploy.yml 管部署。

拆完之后反而引入了新问题——workflow 之间怎么传递 artifact？

ci.yml build 出来的产物要传给 deploy.yml 部署。一开始用 `upload-artifact` + `download-artifact`，但发现跨 workflow 的 artifact 传递不太靠谱——有时候 download 会 404，GitHub 文档里说 artifact 的保留期只有 1 天（workflow_run 触发的情况下）。

后来换了个思路：ci.yml 把构建产物推到 Docker registry，deploy.yml 直接从 registry 拉镜像。其实这才是正道，之前想复杂了。

还有个坑是缓存。pnpm 的依赖缓存用 `actions/cache` 做的，key 是 `pnpm-lock.yaml` 的 hash。但 monorepo 下每个 package 都有自己的依赖，某个 package 加了个新依赖，整个缓存 key 就变了，所有依赖重新下载。折腾了半天也没找到优雅的解法。反正现在就忍着，每次缓存 miss 多等两分钟。

测试覆盖率也有点问题。agent 和 shared 包有单元测试，但 relay 和 app 几乎没有。够呛能短期补上——relay 的逻辑依赖 WebSocket 连接，不好做单元测试，得写集成测试。这事排在 backlog 里了，优先级不高。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "说实话搭得比较糙"
- E15: ✅ — "于是"、"后来"、"其实"、"反正"
- E16: ✅ — "看着头疼"、"不太靠谱"、"折腾了半天"、"够呛能短期补上"
- E18: ✅ — 问题不是列举，而是按时间线叙事
- E19: ✅ — 弯路：artifact跨workflow传递 → 404 → 换Docker registry
- E20: ✅ — "缓存miss多等两分钟"、"测试覆盖率也有点问题...够呛能短期补上"
- **Score: 9/9**

## Run 4 — Spring Boot 3 升级

### Output:

把一个 Spring Boot 2.7 的项目升到了 3.2。比预想的痛苦。

最大的改动是 javax 换成 jakarta。所有 `javax.servlet.*`、`javax.persistence.*`、`javax.validation.*` 的 import 要全部替换成 `jakarta.*`。项目里有 300 多个文件用到了 javax，手动改不现实。

于是写了个 sed 脚本批量替换：

```bash
find src -name "*.java" -exec sed -i 's/javax\.servlet/jakarta.servlet/g; s/javax\.persistence/jakarta.persistence/g; s/javax\.validation/jakarta.validation/g' {} +
```

跑完之后编译报了 47 个错。大部分是 sed 没覆盖到的其他 javax 包——`javax.annotation.PostConstruct` 之类的。这部分只能手动改。

其实 IntelliJ 的 "Migrate to Jakarta" 功能也能做这件事，后来才发现。早知道就不手写 sed 了。

另一个大坑是 Spring Security。Security 6.x 移除了 `WebSecurityConfigurerAdapter`，所有安全配置要改成声明式的 SecurityFilterChain bean。这块改动量虽然不大，但之前对 Security 的理解就停留在"照着 Stack Overflow 抄配置"的水平，突然要重写整个安全配置就有点懵。折腾了一天才搞定。

数据库相关的改动反而没什么，Hibernate 6 的兼容性还行。只有一个地方——原来用 `@Type(type = "json")` 映射 JSON 字段的写法变了，得改成 `@JdbcTypeCode(SqlTypes.JSON)`。

升完之后跑了一遍 regression test，有两个测试挂了——都是 Mock 的 Servlet API 签名变了导致的。改改类型导入就好了。

不过升级指南里提到 Spring Boot 3.2 默认启用了虚拟线程（如果检测到 JDK 21+），我们的服务跑在 JDK 21 上。目前看没什么问题，但对 ThreadLocal 的行为有影响，这块我还没完全搞明白。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅
- E15: ✅ — "于是"、"后来"、"其实"
- E16: ✅ — "有点懵"、"折腾了一天才搞定"、"照着Stack Overflow抄配置"
- E18: ✅ — 不是平行列举，是按遇到的问题顺序叙事
- E19: ✅ — 弯路："手写sed → 后来发现IntelliJ有Migrate功能"
- E20: ✅ — "对ThreadLocal的行为有影响，这块我还没完全搞明白"
- **Score: 9/9**

## Run 5 — htmx 做全栈应用

### Output:

最近在一个内部工具项目上试了 htmx。不写 JavaScript 也能做出还不错的交互。

背景是我们需要一个内部的工单管理系统。功能不复杂——创建工单、分配人、改状态、评论。之前这种需求直接上 React，但这次想试个不一样的路子。

htmx 的核心想法是：让服务器返回 HTML 片段，前端用声明式属性自动替换 DOM。比如一个按钮点击后要加载工单列表：

```html
<button hx-get="/api/tickets" hx-target="#ticket-list" hx-swap="innerHTML">
  加载工单
</button>
<div id="ticket-list"></div>
```

后端（用的 Go + templ）直接返回渲染好的 HTML。没有 JSON 序列化反序列化，没有前端状态管理，没有 virtual DOM diff。

说实话第一天写起来还挺爽的。模板引擎直接拼 HTML，服务端渲染，hydration 什么的完全不用管。

然后第二天就开始踩坑了。

工单状态更新之后，页面上有三个地方要变——列表里的状态标签、顶部的统计数字、侧边栏的待处理计数。htmx 默认一次请求只替换一个 target。于是用了 `hx-swap-oob`（out-of-band swap），让服务器在响应里额外带上要更新的其他 DOM 片段。能实现，但后端的 handler 反而变复杂了——一个更新状态的接口要返回四段 HTML。

后来又遇到搜索+分页的问题。搜索条件和分页参数要同时传给后端，但 htmx 的参数继承规则挺绕的。折腾了半天才搞清楚 `hx-include` 和 `hx-vals` 的区别。

整体体验：简单 CRUD 页面用 htmx 真的很快，代码量比 React 少一半不止。但交互稍微复杂一点（多区域联动、客户端状态、乐观更新）就开始别扭了。这个项目目前还在用 htmx，但评论功能那块操作比较多的地方，我偷偷加了个 Alpine.js 处理客户端逻辑。不算纯粹，但能用。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅
- E15: ✅ — "于是"、"后来"
- E16: ✅ — "挺爽的"、"折腾了半天"、"偷偷加了个"、"但能用"
- E18: ✅ — 问题按时间叙事展开，不是平行枚举
- E19: ✅ — 弯路：htmx简单页面爽 → 复杂交互开始别扭 → 不得不加Alpine.js
- E20: ✅ — "不算纯粹，但能用"
- **Score: 9/9**

---

## Experiment 14 Summary

| Run | E1 | E2 | E6 | E8 | E15 | E16 | E18 | E19 | E20 | Score |
|-----|----|----|----|----|-----|-----|-----|-----|-----|-------|
| 1 K8s OOM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 2 状态管理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 3 CI/CD | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 4 Boot升级 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 5 htmx | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |

**Total: 45/45 (100%)**

**Decision: KEEP** — E18 improved from 3/5 to 5/5. Round 6 done.
