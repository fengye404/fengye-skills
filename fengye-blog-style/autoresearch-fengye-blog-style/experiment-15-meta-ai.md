# Experiment 15 — Baseline with E21/E22/E23 (Meta-AI detection)

## Eval Set (Round 7)
- E8: 第一人称工程叙事
- E15: 有随意连接词 (≥2)
- E16: 有口语化表达 (≥2)
- E18: 无三连平行句
- E19: 有弯路叙事
- E20: 有未完美之处
- E21: 有闲话/个人插叙 — 至少1处与主题无直接技术关系的个人联想/回忆/感慨
- E22: 结尾非"不过+遗留" — 最后一段不能是"不过/但XXX还没搞明白/先不管/以后再说"模板
- E23: 段落开头不重复 — 不能3+连续段落以相同类型连词开头

9 evals × 5 runs = 45

---

## Run 1 — Redis 缓存穿透

### Output:

线上有个接口被刷了。频率不高，每秒大概 50 次，但全是查不存在的用户 ID。

其实一开始没当回事。后来 DBA 发来消息说 MySQL 的 QPS 突然涨了，一查发现全是这个接口打过来的。缓存穿透——请求的 key 在 Redis 里没有，在 MySQL 里也没有，每次都穿透到数据库。

最简单的修法：缓存空值。查不到就往 Redis 里写个空值，过期时间设短一点（比如 60 秒）。

```java
String value = redis.get(key);
if (value != null) {
    return "null".equals(value) ? null : deserialize(value);
}
String dbValue = dao.findById(id);
if (dbValue == null) {
    redis.set(key, "null", 60, TimeUnit.SECONDS);
    return null;
}
redis.set(key, serialize(dbValue), 3600, TimeUnit.SECONDS);
return dbValue;
```

搞定了。但后来想了想，如果攻击者用的是随机 ID（每次都不一样），缓存空值就没用了——Redis 里会堆满无意义的 key。于是又加了一层布隆过滤器。把所有合法的用户 ID 在服务启动时加载到 Bloom Filter 里，请求进来先过一遍 filter，不在里面的直接返回。

说到布隆过滤器，我之前一直以为 Guava 自带的那个 BloomFilter 够用了。后来发现它是本地内存的，每个服务实例各有一份，新增用户的时候只有新增操作所在的那台实例的 filter 会更新。最后换成了 Redis 的 Bloom Filter 模块（RedisBloom），所有实例共享一份。

这事让我想起刚学 Java 的时候，看到"缓存穿透/缓存击穿/缓存雪崩"这三个概念，觉得怎么名字这么像、完全分不清。实际遇到了之后倒是很好区分——穿透是查不存在的 key，击穿是热点 key 过期，雪崩是大面积 key 同时过期。纸上得来终觉浅。

### Evaluation:
- E8: ✅ | E15: ✅ — "其实"、"于是"、"后来" | E16: ✅ — "没当回事"、"搞定了"
- E18: ✅ | E19: ✅ — 弯路：缓存空值 → 发现随机ID无效 → 布隆过滤器 → Guava不共享 → RedisBloom
- E20: ❌ — 所有问题都解决了，没有遗留未完美的地方 (除非"纸上得来终觉浅"算？不算)
- E21: ✅ — "让我想起刚学Java的时候...完全分不清。实际遇到了之后倒是很好区分" 个人回忆
- E22: ✅ — 结尾是个人感慨而非"不过+遗留"
- E23: ✅ — 段落开头不重复
- **Score: 8/9** (E20 FAIL)

## Run 2 — Testcontainers 集成测试

### Output:

之前项目里的集成测试一直是个笑话。

@SpringBootTest 跑起来需要连 MySQL 和 Redis。本地跑没问题——大家都装了 MySQL。但 CI 环境里没有数据库，于是用了 H2 做替代。问题是 H2 和 MySQL 的 SQL 方言不一样，`ON DUPLICATE KEY UPDATE` 之类的语法 H2 不支持。结果就是：本地测试全过，CI 里一堆跑不了的测试被 @Disabled 了。

后来发现了 Testcontainers。核心思路是在测试启动时用 Docker 拉一个真实的 MySQL 容器，测试完销毁。

配置不复杂：

```java
@Container
static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0")
    .withDatabaseName("test")
    .withUsername("test")
    .withPassword("test");

@DynamicPropertySource
static void props(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", mysql::getJdbcUrl);
}
```

第一次跑忽然觉得世界清净了——所有之前因为 H2 兼容性而 @Disabled 的测试全部解封，而且跑的是真实 MySQL，结果可信。

但速度是个问题。每个测试类启动一个 MySQL 容器要 5 秒，我们有 30 多个集成测试类。如果每个都启动自己的容器，光启动容器就要两分钟多。于是改成了 singleton 模式——所有测试类共享一个容器，用一个抽象基类控制生命周期。

还有个没预料到的坑：CI 的 GitHub Actions runner 默认 Docker 可用，但如果用了 self-hosted runner，Docker 不一定装了。有个同事的 runner 跑在公司内网服务器上，没装 Docker，测试直接跳过（Testcontainers 检测不到 Docker 会自动 skip 而不是 fail）。悄无声息地跳过比直接报错更可怕。

### Evaluation:
- E8: ✅ | E15: ✅ — "于是"、"后来" | E16: ✅ — "一直是个笑话"、"世界清净了"
- E18: ✅ | E19: ✅ — 弯路：H2替代 → 方言不兼容 → Testcontainers
- E20: ✅ — "悄无声息地跳过比直接报错更可怕"
- E21: ✅ — "忽然觉得世界清净了" 个人感受
- E22: ✅ — 结尾是对hidden failure的警告，不是"不过+遗留"模板
- E23: ✅
- **Score: 9/9**

## Run 3 — TermPilot 安全审计

### Output:

前段时间给 TermPilot 做了一次安全自查。说是审计有点夸张——其实就是拿 OWASP 的 checklist 对着项目过了一遍。

最明显的问题是 token 传输方式，之前的文章提过了。第二个问题是命令注入——relay 会把前端发来的输入转发给 shell。如果没有任何过滤，用户可以通过 terminal 执行任何命令。

不过这个"漏洞"其实是设计如此。TermPilot 的定位就是远程终端，用户本来就应该能执行任意命令。安全边界不在命令过滤，而在认证——只有拿到 token 的人才能连上来。

但认证之外还有一层我之前忽略的：WebSocket 消息的大小限制。如果有人发一个 100MB 的消息过来，relay 的内存会直接爆掉。于是加了个 `maxPayload` 限制，设成了 1MB。

跑了一遍 `npm audit`，发现有 3 个高危漏洞。点进去一看——全是间接依赖里的，而且都是 `ReDoS`（正则表达式拒绝服务）。修法是升级对应的直接依赖。有一个升不了——那个包两年没更新了。反正实际被利用的概率很低，先记个 TODO。

做完之后的感受是：安全这事永远做不完。你以为堵住了所有洞，但 `npm audit` 每跑一次都能蹦出新的 CVE。有点像打地鼠。

### Evaluation:
- E8: ✅ | E15: ✅ — "其实"、"于是"、"反正" | E16: ✅ — "有点夸张"、"有点像打地鼠"
- E18: ✅ | E19: ✅ — 弯路：以为命令注入是问题 → 其实designed intention → 发现真正问题是消息大小
- E20: ✅ — "有一个升不了...先记个TODO"
- E21: ✅ — "有点像打地鼠" 个人比喻/感慨
- E22: ✅ — 结尾是个人感慨而非"不过+遗留"
- E23: ✅
- **Score: 9/9**

## Run 4 — Bun 替代 Node.js

### Output:

上个月把一个小项目从 Node.js 换到 Bun 跑了两周。

起因是看到 Bun 1.0 发布的新闻。之前一直觉得"又一个 JS runtime"，没太在意。后来在 Twitter 上刷到好几个性能对比，HTTP server 的吞吐量比 Node 高好几倍。好奇心驱动，拿了个最简单的内部 API 服务试水。

迁移过程出乎意料地顺利。

`package.json` 不用改，`bun install` 装依赖比 npm 快了十倍不止（本地缓存命中的情况下几乎是瞬间）。Express 应用直接 `bun run index.ts` 就能跑——Bun 原生支持 TypeScript，不用 ts-node 也不用先编译。

这个体验让我想起当年从 Webpack 换到 Vite 的感觉。那种"以前忍受的痛苦原来不是必须的"的顿悟。

但好景不长。跑了三天之后，生产环境突然开始报 502。排查发现是 Bun 的 HTTP 实现在处理某种 chunked transfer encoding 的响应时有 bug。GitHub Issues 里已经有人报了，状态是 open。

只好切回 Node。

反正 Bun 的 DX 确实一流——启动快、装包快、不用编译 TypeScript。但稳定性还差一些。等下个大版本再试。

### Evaluation:
- E8: ✅ | E15: ✅ — "后来"、"反正" | E16: ✅ — "没太在意"、"好奇心驱动"、"好景不长"
- E18: ✅ | E19: ✅ — 弯路：Bun一切顺利 → 第三天502 → 切回Node
- E20: ✅ — "稳定性还差一些"
- E21: ✅ — "让我想起当年从Webpack换到Vite的感觉。那种'以前忍受的痛苦原来不是必须的'的顿悟" 
- E22: ❌ — "但稳定性还差一些。等下个大版本再试。" → 这是 "不过+暂时先不管" 的变体。FAIL。
- E23: ✅
- **Score: 8/9** (E22 FAIL)

## Run 5 — 自建 Git Server (Gitea)

### Output:

公司有几个不能放 GitHub 的项目（合同原因），之前是用的 GitLab CE。GitLab 太重了——光跑起来就要 6GB 内存，CI runner 另算。于是换成了 Gitea。

Gitea 用 Go 写的，单二进制文件，默认跑起来内存占用不到 200MB。部署极其简单——下载二进制，配个 `app.ini`，跑起来就能用。

数据库选了 SQLite（又是 SQLite）。反正只有十来个人用，写并发基本为零。

迁移 GitLab 的仓库到 Gitea 花了大概一天。Gitea 自带 GitLab migration 功能，填上 GitLab 的 URL 和 access token 就能把 repo 连带 issues 和 PR 一起导过来。大部分仓库导入很顺利，有两个超过 2GB 的仓库（屎山遗产）超时了，最后是直接 `git push --mirror` 推过去的，issues 就手动重建了几个重要的。

最让人头疼的是权限配置。GitLab 的权限模型和 Gitea 不完全对应——GitLab 有 Group、Project、Personal Namespace 三级，Gitea 只有 Organization 和 Repository 两级。有些 GitLab Group 的嵌套权限在 Gitea 里表达不了。

妥协方案：把 GitLab 的 Group 打平成 Gitea 的 Organization，原来嵌套在子 Group 里的仓库全挪到顶层 Org 下。权限用 Team 机制重新分配。

做完这件事想起来以前在学校搭各种服务的日子——Nextcloud、Bitwarden、Gitea，那会儿折腾纯粹是好玩。现在折腾是因为甲方不让用 GitHub。心态完全不一样了。

### Evaluation:
- E8: ✅ | E15: ✅ — "于是"、"反正" | E16: ✅ — "太重了"、"屎山遗产"、"折腾纯粹是好玩"
- E18: ✅ | E19: ✅ — 弯路：Gitea自带migration → 大仓库超时 → 手动push
- E20: ✅ — "有些GitLab Group的嵌套权限在Gitea里表达不了" + 妥协方案
- E21: ✅ — "想起来以前在学校搭各种服务的日子——Nextcloud、Bitwarden、Gitea，那会儿折腾纯粹是好玩。现在折腾是因为甲方不让用GitHub。心态完全不一样了。"
- E22: ✅ — 结尾是个人感慨/回忆，不是"不过+遗留"
- E23: ✅
- **Score: 9/9**

---

## Experiment 15 Summary

| Run | E8 | E15 | E16 | E18 | E19 | E20 | E21 | E22 | E23 | Score |
|-----|----|----|-----|-----|-----|-----|-----|-----|-----|-------|
| 1 Redis | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | 8/9 |
| 2 Testcontainers | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 3 安全审计 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 4 Bun | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | 8/9 |
| 5 Gitea | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |

**Total: 43/45 (95.6%)**

**Failure analysis:**
- E20 有未完美: 4/5 — Run 1 resolved all problems cleanly
- E22 结尾非模板: 4/5 — Run 4 ("等下个大版本再试") still fits the "defer" pattern
- Both are intermittent; the pattern tendency is still there.
