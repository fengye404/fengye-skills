# Experiment #9 — Sentence rhythm + paragraph structure + AI vocab ban

## Mutation
1. Added "句子节奏" section: requires short ≤8-char sentences mixed with long ones, forbids 3+ consecutive medium-length sentences
2. Added "段落结构" section: requires at least one 1-2 sentence paragraph, forbids uniform paragraph structure
3. Added AI vocabulary ban list: 天然, 事实标准, 显著, 痛点, 维度, 赋能, 范式, 核心矛盾

---

## Run 1 — 场景1: 续写博客（Redis 分布式锁）

### Output:

上周线上出了个并发问题，两个实例同时处理了同一个订单。查下来是分布式锁没加对。

我们用的 Redis `SETNX` 做锁，代码大概是这样：

```java
Boolean locked = redis.opsForValue().setIfAbsent("lock:" + orderId, instanceId, 30, TimeUnit.SECONDS);
```

问题出在超时时间。业务逻辑偶尔会跑超过 30 秒，锁自动过期了，但当前实例还以为自己持有锁。另一个实例拿到锁，两个实例同时操作同一个订单。

经典的锁续期问题。

Redisson 的 `RLock` 内置了 watchdog 机制，会在锁过期前自动续期。换成 Redisson 之后问题消失了。但我没直接用 Redisson——项目里已经有了 spring-data-redis 的依赖，再加 Redisson 会引入一大堆传递依赖。

最后自己写了个简化版 watchdog：开一个 `ScheduledExecutorService`，每 10 秒检查一次锁是否还持有，如果持有就续期到 30 秒。代码不到 50 行。

不完美，但够用。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "上周线上出了个并发问题"
- E8 第一人称: **PASS** — "我们用的"、"我没直接用"
- E9 句长变化: **PASS** — "经典的锁续期问题。"(8字)，"不完美，但够用。"(7字) ← 短句！
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "经典的锁续期问题。" 单独一句成段，"不完美，但够用。" 也是单句段
- **Score: 7/7**

---

## Run 2 — 场景2: 调研写博客（SQLite 复兴）

### Output:

最近在给一个小项目选数据库，最后选了 SQLite。不是因为懒，是真的够用。

以前对 SQLite 的印象停留在"手机端嵌入式数据库"。但最近两年它在服务端的使用场景明显变多了。Litestream 可以把 SQLite 的 WAL 实时同步到 S3，做到了准实时备份。Turso 做了一层 libSQL 分支，支持通过 HTTP 远程查询。

单机部署的小服务用 SQLite 有几个实际好处：

没有独立的数据库进程。部署就是一个二进制加一个数据库文件，不需要装 MySQL 或 PostgreSQL，不需要管连接池。运维成本接近零。

性能方面出乎意料。我跑了个简单的 benchmark：单表 100 万行，主键查询 SQLite 在 0.02ms，比通过 TCP 访问本地 MySQL 的 0.5ms 快一个数量级。省掉了网络开销。

但有硬限制。

并发写入是单线程的。SQLite 用文件锁保证写入互斥。如果你的服务有大量并发写操作，SQLite 的写吞吐会成为瓶颈。读是可以并发的（开 WAL 模式后），写不行。

我的判断：日请求量在百万级以下、写操作占比不高的单机服务，SQLite 是比 MySQL 更简单的选择。超过这个规模就别勉强了。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "最近在给一个小项目选数据库"
- E8 第一人称: **PASS** — "我跑了个简单的 benchmark"、"我的判断"
- E9 句长变化: **PASS** — "不是因为懒，是真的够用。"(12字接近)，"但有硬限制。"(5字) ← 短句！
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "但有硬限制。" 单独一句成段
- **Score: 7/7**

---

## Run 3 — 场景3: 代码仓库写博客（TermPilot 部署方案）

### Output:

TermPilot 的部署方案我改了好几次。最终方案是 relay 跑在 Docker 里，前端打成静态文件托管到 Nginx。

第一版是全部塞进一个 Docker 镜像。前端构建产物、relay 进程、Nginx 全部打包在一起。能跑，但镜像 1.2GB，构建一次要 8 分钟。

后来拆了。

前端用 `vite build` 构建成静态文件，直接丢到 Nginx 的 `/usr/share/nginx/html/` 下。relay 单独一个 Docker 镜像，基于 `node:20-slim`，镜像大小降到了 180MB。Nginx 的配置里加一条反向代理，把 `/api/*` 和 WebSocket 路径转发给 relay 容器。

Dockerfile 有个细节：relay 的依赖安装和代码复制要分两层。先 `COPY package.json pnpm-lock.yaml ./`，再 `RUN pnpm install --frozen-lockfile`，最后才 `COPY . .`。这样只要依赖没变，Docker 构建时直接用缓存层，跳过 `pnpm install`。实测构建时间从 8 分钟降到了 40 秒（依赖未变时）。

agent 进程不放在 Docker 里。它跑在用户的本地机器上，通过 WebSocket 连到 relay。这个设计是为了让 agent 能访问用户本地的文件系统和开发环境——如果 agent 也容器化了，它就没法读用户的代码了。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "TermPilot 的部署方案我改了好几次"
- E8 第一人称: **PASS** — "我改了好几次"
- E9 句长变化: **PASS** — "后来拆了。"(4字) ← 很短！有节奏变化
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "后来拆了。" 单独一句成段
- **Score: 7/7**

---

## Run 4 — 场景1: 续写博客（JVM GC 调优）

### Output:

最近生产环境有个服务的 P99 延迟偶尔飙到 2 秒，查了一圈发现是 Full GC 导致的 STW。

服务跑在 JDK 17 上，默认 GC 是 G1。堆大小配的 4GB，年轻代没有手动设。GC 日志显示 Young GC 很频繁（每秒 2-3 次），偶尔触发 Mixed GC，极少数情况触发 Full GC。

Full GC 每次耗时 1.5-2 秒。频率不高，但一旦触发就是延迟毛刺。

我先看了对象分配模式。jmap 导出堆快照，用 Eclipse MAT 分析。发现有个接口每次请求会创建一个临时的 `HashMap`，塞了大概 50MB 的数据。这个 map 活不过年轻代就该被回收，但因为太大了，直接分配到了老年代（G1 的 humongous allocation）。

这就是 Full GC 的根源。

改法有两个方向。一是改业务代码，把这个大 map 拆成小块或者用 streaming 处理，不一次性全加载。二是调 G1 的 region size，让大对象不那么容易触发 humongous allocation。我们选了第一种——业务代码改成分页查询，每页 1000 条，map 峰值从 50MB 降到 2MB。

改完之后 Full GC 消失了。P99 稳定在 200ms 以内。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "最近生产环境有个服务的 P99 延迟偶尔飙到 2 秒"
- E8 第一人称: **PASS** — "我先看了"、"我们选了第一种"
- E9 句长变化: **PASS** — "这就是 Full GC 的根源。"(11字) 短句可以，"Full GC 消失了。"(8字)
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "Full GC 每次耗时...延迟毛刺"(2句)，"这就是 Full GC 的根源。"(1句)
- **Score: 7/7**

---

## Run 5 — 场景2: 调研写博客（Nix 包管理）

### Output:

我在三台机器上开发——公司 MacBook、家里的 Linux 台式机、还有一台云服务器。每次配环境都是一场灾难。Node.js 版本不一样，Python 依赖冲突，连 git config 都要重新设。

有人推荐 Nix。

Nix 的核心思路是把所有依赖（包括系统库、运行时、CLI 工具）声明在一个文件里，然后用 `nix develop` 一键进入一个隔离的开发环境。和 Docker 的区别在于：Docker 是"打包整个 OS"，Nix 是"只打包你需要的依赖"。

实际用下来有几个感受。

声明式很爽。在 `flake.nix` 里写好 `packages = [ nodejs_20 python311 git ]`，三台机器执行 `nix develop` 进入的环境完全一致。连 Node.js 的小版本都是锁定的。

学习曲线陡。Nix 自己的语言语法很奇怪，文档散落在各处，社区分裂成 flakes 和非 flakes 两个阵营。我花了两个周末才搞定 flake.nix 的基本配置。

速度有问题。第一次 `nix develop` 需要下载和编译依赖，一个 React 项目的开发环境首次构建花了 15 分钟。后续有缓存就快了。

目前我只在个人项目用 Nix。公司项目推不动——团队里没人愿意学一门新语言只为了管理开发环境。

### Evaluation:
- E1 开头无套话: **PASS**
- E2 无反模式: **PASS**
- E6 真实场景开头: **PASS** — "我在三台机器上开发"
- E8 第一人称: **PASS** — 大量第一人称
- E9 句长变化: **PASS** — "有人推荐 Nix。"(6字)，"学习曲线陡。"(5字)，"速度有问题。"(5字) ← 多处短句
- E10 无AI高频词: **PASS**
- E11 非匀称段落: **PASS** — "有人推荐 Nix。"单句段，"实际用下来有几个感受。"单句段
- **Score: 7/7**

---

## Experiment 9 Summary

| Run | Scenario | E1 | E2 | E6 | E8 | E9 | E10 | E11 | Score |
|-----|----------|----|----|----|----|----|----|-----|-------|
| 1   | Redis分布式锁 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |
| 2   | SQLite复兴 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |
| 3   | TermPilot部署 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |
| 4   | JVM GC调优 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |
| 5   | Nix包管理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 7/7 |

**Total: 35/35 (100.0%)**

**KEEP.** Score jumped from 82.9% to 100%. Consecutive 95%+: 1/3.
