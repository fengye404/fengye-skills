# Experiments 11-17 — Deep Anti-AI Optimization (Rounds 4-10)

## Eval Set (final 9 evals)
- E1: 开头无套话
- E2: 无反模式句式
- E6: 真实场景开头
- E8: 第一人称工程叙事
- E9: 句长节奏变化 (≤8字短句 + ≥35字长句)
- E10: 无AI高频词 (天然/事实标准/显著/痛点/维度/赋能/范式/核心矛盾)
- E11: 有非匀称段落 (至少1个1-2句短段)
- E15: 有随意连接词 (于是/后来/反正/其实/说白了/结果/折腾 至少1个)
- E16: 有口语化表达 (搞定/折腾/有点X/挺X的/随手/不太靠谱 至少1处)

Max: 9 × 5 = 45

---

# Experiment 11 — Baseline with E15/E16

## Run 1 — 场景1: 续写博客（Docker 多阶段构建）

### Output:

最近在优化公司一个 Java 服务的 Docker 镜像，从 1.2GB 压到了 180MB。

之前的 Dockerfile 很粗暴——直接用 `maven:3.9-eclipse-temurin-17` 作为基础镜像，在里面编译打包再运行。Maven 加 JDK 的完整镜像就有 800MB，加上项目依赖，最终镜像 1.2GB。拉取一次要好几分钟。

多阶段构建的思路是把编译和运行分开。第一阶段用 Maven 镜像编译出 jar，第二阶段用 `eclipse-temurin:17-jre-alpine` 只装 JRE，把 jar 拷进去。

```dockerfile
FROM maven:3.9-eclipse-temurin-17 AS build
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-alpine
COPY --from=build target/app.jar /app.jar
CMD ["java", "-jar", "/app.jar"]
```

有个细节：`mvn dependency:go-offline` 要放在 `COPY src` 之前。这样只要 pom.xml 没变，依赖下载那一层就走缓存。否则每次改代码都要重新下载依赖，构建时间翻倍。

最终镜像 180MB。构建时间从 8 分钟降到了 2 分钟（有缓存的情况下）。

### Evaluation:
- E1: **PASS** | E2: **PASS** | E6: **PASS** | E8: **PASS** — "之前的Dockerfile很粗暴"
- E9: **FAIL** — 缺少≤8字短句
- E10: **PASS** | E11: **FAIL** — 所有段落3+句
- E15: **FAIL** — 无随意连接词
- E16: **FAIL** — "很粗暴"接近口语但不够，缺少明显口语表达
- **Score: 5/9**

## Run 2 — 场景2: 调研（Rust 生态 2026 状态）

### Output:

去年底开始学 Rust，到现在半年了，说说感受。

语言本身学习曲线确实陡。所有权系统前两周基本是在和编译器吵架。后来慢慢找到感觉了——其实编译器报错信息非常精确，告诉你哪里违反了 borrow rules，只是刚开始看不懂。

生态方面，Web 框架 Actix 和 Axum 两家打架。我选了 Axum，因为和 tokio 生态更紧密。写起来的感觉有点像 Express.js——定义路由、挂中间件、处理请求。区别在于类型系统帮你挡住了大多数运行时错误。

折腾了一个月搞定了一个玩具 API 服务。

不过有些地方还是挺痛苦的。async trait 到现在还需要 `#[async_trait]` 宏来 workaround，编译时间长得离谱，一个小项目全量编译要 3 分钟。增量编译快一些，但改了某些 crate 的依赖还是会触发大面积重编译。

总体判断：写 CLI 工具和性能敏感的服务值得用 Rust，普通 CRUD 服务用 Rust 纯属自虐。

### Evaluation:
- E1: **PASS** | E2: **PASS** | E6: **PASS** | E8: **PASS**
- E9: **PASS** — "折腾了一个月搞定了一个玩具 API 服务。" 中等短句，"后来慢慢找到感觉了" 长句。BUT ≤8字短句？没有明显的。**FAIL**
- E10: **PASS** | E11: **PASS** — "折腾了一个月搞定了一个玩具API服务。" 单句段
- E15: **PASS** — "后来慢慢找到感觉了"、"其实编译器报错信息非常精确"、"折腾了一个月"
- E16: **PASS** — "折腾了一个月搞定了"、"有点像 Express.js"、"挺痛苦的"、"纯属自虐"
- **Score: 7/9** (E9 FAIL)

## Run 3 — 场景3: 代码仓库（TermPilot WebSocket 断连重连）

### Output:

TermPilot 上线之后遇到的第一个用户投诉是：终端突然断开了，刷新页面才能恢复。

查了下是 WebSocket 连接超时断开。Nginx 的 `proxy_read_timeout` 默认 60 秒，如果 60 秒内没有消息往来，Nginx 就关掉 WebSocket 连接。用户打开终端然后去泡了杯咖啡回来，连接已经断了。

最简单的修法是加心跳。前端每 30 秒发一个 ping 帧，relay 回 pong。保持连接活跃。

但光有心跳还不够。

网络抖动、VPN 切换、笔记本合上盖子——这些场景心跳也救不了。必须做自动重连。

重连逻辑：前端检测到 WebSocket 关闭后，等 1 秒重连。失败了等 2 秒，再失败 4 秒，指数退避，上限 30 秒。重连成功后恢复之前的终端 session——relay 那边 session 没销毁（设了 5 分钟的 session 过期时间），前端只需要重新 attach 到同一个 session id 就行。

说白了就是：心跳防超时，重连防断线。

折腾了两天才把所有边界情况处理完。最烦的是"半关闭"状态——WebSocket 的 `readyState` 显示 OPEN 但实际上底层 TCP 连接已经断了。检测方式是给每个 ping 帧设 5 秒超时，超时没收到 pong 就主动关闭并触发重连。

### Evaluation:
- E1: **PASS** | E2: **PASS** | E6: **PASS** | E8: **PASS**
- E9: **PASS** — "但光有心跳还不够。"(9字接近)，更重要："说白了就是：心跳防超时，重连防断线。" 这句有内部的短节奏
- E10: **PASS** | E11: **PASS** — "但光有心跳还不够。" 单句段
- E15: **PASS** — "说白了就是"、"折腾了两天"
- E16: **PASS** — "折腾了两天才把所有边界情况处理完"、"最烦的是"
- **Score: 9/9**

## Run 4 — 场景1: 续写博客（MySQL 索引失效排查）

### Output:

昨天线上一个查询突然变慢了，从 50ms 涨到 3 秒。

EXPLAIN 一看，全表扫描。但这个查询明明有索引。

查了 `SHOW INDEX FROM orders`，索引在。再看 EXPLAIN 的 `key` 列，是 NULL——MySQL 选择了不用这个索引。

原因是隐式类型转换。查询条件 `WHERE order_no = 12345678`，order_no 字段是 VARCHAR，但传进来的值是 INT。MySQL 做了隐式转换，index 就失效了。

改成 `WHERE order_no = '12345678'` 就好了。

这种问题追根溯源到 MyBatis 的 XML 映射。#{orderNo} 绑定的参数是 Long 类型，MyBatis 直接把数字传给了 MySQL，没有加引号。改法是在 Java 侧把参数类型改成 String，或者在 XML 里显式指定 `#{orderNo, jdbcType=VARCHAR}`。

还有一种常见的索引失效：对索引列用了函数。`WHERE DATE(create_time) = '2026-03-27'` 会导致 create_time 上的索引失效，改成范围查询 `WHERE create_time >= '2026-03-27' AND create_time < '2026-03-28'` 就行。

反正经验就是：慢查询先看 EXPLAIN，EXPLAIN 先看 key 列。

### Evaluation:
- E1: **PASS** | E2: **PASS** | E6: **PASS** | E8: **PASS**
- E9: **PASS** — "改成...就好了。"(短)，"索引在。"(3字)
- E10: **PASS** | E11: **PASS** — "改成...就好了。" 单句段，"查了...索引在。再看..." 2句段
- E15: **PASS** — "反正经验就是"
- E16: **PASS** — "就好了"
- **Score: 9/9**

## Run 5 — 场景2: 调研（Tailwind CSS 是好是坏）

### Output:

前几天团队里又吵了一次 Tailwind CSS 要不要引入的问题。我是偏支持的那一边。

反对的同事觉得 `class="flex items-center justify-between px-4 py-2 bg-gray-100 rounded-lg"` 太丑了，HTML 里全是 class 名，可读性差。这个批评是对的。

但实际写起来——特别是配合组件化框架——这个问题没那么严重。

一个 React 组件里的 JSX 本来就只有几十行，class 名长一点无所谓。真正影响可读性的是几千行的全局 CSS 文件，同事们各写各的 class 名，命名冲突、样式覆盖、dead CSS 堆积。Tailwind 把这些问题直接消除了。

我在个人项目里用了半年。生产力确实提升了。以前写一个组件要在 CSS 文件里来回跳，现在直接在 JSX 里写完。改样式不用担心影响别的组件。

有个前提：你得配合 Prettier 的 tailwindcss 插件做 class 排序，否则 class 列表会变成灾难。

不过有些场景 Tailwind 确实不合适——复杂动画、主题切换、需要大量 CSS 变量的设计系统。这些场景还是老老实实写 CSS。

### Evaluation:
- E1: **PASS** | E2: **PASS** | E6: **PASS** — "前几天团队里又吵了一次"
- E8: **PASS** — "我是偏支持的那一边"、"我在个人项目里用了半年"
- E9: **FAIL** — 缺少≤8字的短促断句
- E10: **PASS** | E11: **PASS** — "但实际写起来——..." 和代码比较，部分段落2句
- E15: **PASS** — "不过有些场景"、"其实" (无——其实没出现。检查：反正/后来/其实/于是... 没有。"不过"算不算？不在列表里)。重新检查：于是/后来/反正/其实/说白了/结果/折腾——都没出现。**FAIL**
- E16: **PASS** — "太丑了"、"无所谓"、"老老实实写CSS"
- **Score: 7/9** (E9, E15 FAIL)

---

## Experiment 11 Summary

| Run | E1 | E2 | E6 | E8 | E9 | E10 | E11 | E15 | E16 | Score |
|-----|----|----|----|----|----|----|-----|-----|-----|-------|
| 1 Docker多阶段 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | 5/9 |
| 2 Rust生态 | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | 7/9 |
| 3 TermPilot重连 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 4 MySQL索引 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 5 Tailwind | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | 7/9 |

**Total: 37/45 (82.2%)**

**Failure analysis:**
- E9 句长变化: 2/5 — model still defaults to uniform medium sentences in some outputs
- E15 随意连接词: 3/5 — some outputs are "professionally casual" but miss the truly casual connectors
- E11 非匀称段落: 4/5
- E16 口语化: 4/5

**Primary weakness:** E9 and E15 — sentence rhythm and casual voice still inconsistent.

---

# Experiment 12 — Mutation: strengthen casual voice instructions

## Mutation
Added explicit casual connector examples and strengthened sentence rhythm rules in skill.

(mutation details in next experiment file)
