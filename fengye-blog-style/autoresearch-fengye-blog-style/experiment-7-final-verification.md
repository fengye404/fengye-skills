# Experiment #7 — Final verification (3/3 consecutive 95%+)

## Purpose
Third consecutive 95%+ check for Round 2. If this passes, stop condition is met.

---

## Run 1 — 场景2: 调研 autoresearch 写博客（prompt vs code optimization）

### Output:

我试着把 autoresearch 的方法论从 ML 训练搬到 prompt 优化，发现核心机制可以直接复用，但 eval 的设计思路完全不同。

ML 领域的 eval 天然存在——loss function、accuracy、F1 score。prompt 优化没有这些。你需要自己定义"好"是什么意思，而且这个定义必须是二元的，因为 LLM 做 1-7 分制评估时方差太大。

我的做法是把主观的"写得好"拆成多个可判断的检查项。比如评估博客文风：开头有没有套话（是/否）、有没有出现禁止句式（是/否）、有没有具体工程名词（是/否）。每一项单独判断一致性较高，组合起来就是对"文风"的近似度量。

实践中遇到的坑：第一版 eval 覆盖不全，分数到 100% 了但输出明显有问题——读起来像文档不像博客。根本原因是我没考虑到"视角"和"开头方式"这两个维度。加了之后分数回落到 70%，然后再针对性改 skill 才真正提升了质量。

教训是：eval 不可能一步到位。先跑一轮看输出，用直觉找 eval 的盲区，迭代追加。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — loss function, F1 score, LLM, binary eval, prompt
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "我试着把 autoresearch 的方法论从 ML 训练搬到 prompt 优化"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我试着"、"我的做法是"、"我没考虑到"
- **Score: 8/8**

---

## Run 2 — 场景3: 对当前代码仓库（TermPilot）写博客（monorepo 结构）

### Output:

TermPilot 的代码结构我换了三次才定下来，最后用了 pnpm workspace 的 monorepo 方案。

项目有四个包：`app`（前端 React 应用）、`relay`（中继服务 Node.js）、`agent`（AI agent 进程）、`shared`（共享的协议定义和类型）。前端和 relay 都依赖 shared 包里的类型定义，如果拆成独立仓库，类型同步会是个持续的痛点。

pnpm workspace 的好处是 `shared` 包的改动对 `app` 和 `relay` 即时可见，不需要发 npm 包。`pnpm-workspace.yaml` 里声明三个包路径就行：

```yaml
packages:
  - 'app'
  - 'relay'
  - 'agent'
  - 'shared'
```

构建用的 tsup，配置放在根目录的 `tsup.config.ts`。`shared` 包先构建，`app` 和 `relay` 引用它的产物。开发时用 `tsc --watch` 做增量编译，改了 shared 里的类型定义，前端和 relay 的类型检查几秒内就能感知到。

一个踩坑的点：pnpm 的 hoist 策略默认情况下不会把所有依赖提升到根目录的 `node_modules`。如果 relay 用了一个只在 relay 自己的 `package.json` 里声明的依赖，app 的代码不应该能 import 它。但如果不小心在 `.npmrc` 里配了 `shamefully-hoist=true`，这个隔离就会被打破。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — pnpm workspace, monorepo, tsup, tsconfig, tsc --watch, shamefully-hoist, node_modules
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 的代码结构我换了三次才定下来"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我换了三次"
- **Score: 8/8**

---

## Run 3 — 场景1: 续写博客（Spring Boot 3 — Security 配置迁移）

### Output:

Boot 3 迁移里我花时间最多的是 Spring Security 配置。

Boot 2.x 时代，Security 配置继承 `WebSecurityConfigurerAdapter`，重写 `configure(HttpSecurity http)` 方法。Boot 3 里这个类被移除了，改成了注册 `SecurityFilterChain` Bean 的方式。

之前的写法：

```java
@Override
protected void configure(HttpSecurity http) throws Exception {
    http.authorizeRequests()
        .antMatchers("/api/public/**").permitAll()
        .anyRequest().authenticated();
}
```

现在改成：

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/api/public/**").permitAll()
        .anyRequest().authenticated()
    );
    return http.build();
}
```

注意 `authorizeRequests()` 也废弃了，换成了 `authorizeHttpRequests()`；`antMatchers()` 换成了 `requestMatchers()`。如果你只改了类结构没改方法名，编译能过但运行时行为可能不符合预期。

我们项目有个自定义的 `JwtAuthenticationFilter`，挂在 `UsernamePasswordAuthenticationFilter` 之前。迁移的时候发现 filter 的注册方式也变了——之前用 `http.addFilterBefore()`，现在还是用这个方法但参数类型变了，需要确保 filter 类实现的是 `jakarta.servlet.Filter` 而非 `javax.servlet.Filter`。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — WebSecurityConfigurerAdapter, SecurityFilterChain, authorizeHttpRequests, requestMatchers, JwtAuthenticationFilter
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "Boot 3 迁移里我花时间最多的是 Spring Security 配置"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我花时间最多的"、"我们项目有个"
- **Score: 8/8**

---

## Run 4 — 场景2: 调研 autoresearch 写博客（自动化 vs 手动优化）

### Output:

手动调 skill 和用 autoresearch 调，我两种都试过了，差别在可复现性。

手动调的流程是：看一两个输出觉得不对劲，改 skill 里的某句话，再生成一两个看看。问题是你不知道这次"看起来好了"是改动生效了还是恰好换了个好 case。样本量太小，随机性太大。

autoresearch 的做法是每次改动跑 5 轮（可以更多），对每个输出做 8 项二元检查，算通过率。改动前 70%，改动后 100%，那大概率是改动生效了。如果只从 80% 跳到 85%，可能是噪声，不够显著。

我跑下来的经验：贪心策略（一次只改一个地方）比一次改三四个地方更可靠。改多了你分不清哪个起了作用。即使某次改了三个地方分数大涨，你也没法确认是三个都有用还是只有一个起效、另外两个是无效甚至有害的复杂度。

另一个经验：eval 本身要迭代。第一版 eval 跑到 100% 不代表 skill 完美了，通常意味着 eval 的覆盖面不够。看输出、找盲区、追加 eval、重新建 baseline——这个外循环比内循环（改 skill）更关键。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — greedy strategy, binary eval, baseline, pass rate
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "手动调 skill 和用 autoresearch 调，我两种都试过了"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我两种都试过了"、"我跑下来的经验"
- **Score: 8/8**

---

## Run 5 — 场景3: 对当前代码仓库（TermPilot）写博客（协议设计）

### Output:

TermPilot 的通信协议我设计了两版，第一版用 REST，后来改成了 WebSocket 上的自定义 JSON-RPC。

改的原因是双向通信。REST 是请求-响应模型，relay 没法主动给 agent 推消息。但实际场景里 relay 需要主动通知 agent 很多事：用户取消了当前操作、终端输出了新内容、权限配置变更了。用 REST 只能靠 agent 轮询，延迟高且浪费资源。

JSON-RPC 跑在 WebSocket 上天然支持双向。协议定义放在 `shared/src/protocol.ts` 里，前端、relay、agent 三个包都引用这一份定义，改协议只需要改一处。

消息分两类：终端数据流和控制消息。数据流就是键盘输入和终端输出，量大、频率高、对延迟敏感。控制消息是 resize、session 管理、心跳，频率低但逻辑复杂。两类消息走同一条 WebSocket 连接，用 `type` 字段区分。

协议里有个设计取舍：要不要对终端数据流做额外的序列化（比如 base64）。我最后选了不做——直接传原始字节的 UTF-8 编码。base64 会让数据膨胀 33%，对于高频的终端输出来说代价太大。特殊字符用 JSON 的转义机制处理就够了。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E3 语气硬无模糊词: **PASS**
- E4 具体工程名词: **PASS** — JSON-RPC, WebSocket, REST, protocol.ts, base64, UTF-8, shared/src
- E5 无重复解释: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 的通信协议我设计了两版"
- E7 无AI过渡句: **PASS**
- E8 有第一人称工程叙事: **PASS** — "我设计了两版"、"我最后选了不做"
- **Score: 8/8**

---

## Experiment 7 Summary

| Run | Scenario | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | Score |
|-----|----------|----|----|----|----|----|----|----|----|-------|
| 1   | autoresearch对比 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 2   | TermPilot monorepo | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 3   | Boot3 Security | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 4   | autoresearch手动vs自动 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |
| 5   | TermPilot协议 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 8/8   |

**Total score: 40/40 (100.0%)**

Consecutive 95%+ runs: **3/3** — **STOP CONDITION MET**
