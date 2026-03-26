# Experiment 12 — Mutation: Casual Voice + Stronger Rhythm

## Mutation Applied
1. 句子节奏: Changed "穿插短句" to "每篇至少3处≤8字短句" with more examples
2. NEW 口语化语气 section with 3 subsections:
   - 随意连接词: Must use ≥2 from [于是/后来/反正/其实/说白了/结果/然后]
   - 口语化表达: Must have ≥2 colloquial expressions with word bank
   - 对比示例 table: AI味 vs 人味

## Run 1 — Docker Compose 多服务编排

### Output:

上周把公司的一个单体项目拆成了三个服务，本地开发环境从 "直接跑 main 方法" 变成了 "要启动 5 个东西才能跑起来"。折腾了一天才用 Docker Compose 搞定。

先说问题。三个服务分别依赖 MySQL、Redis 和 RabbitMQ。之前单体的时候，本地装一个 MySQL 一个 Redis 就够了。拆完之后每个服务要自己的配置，端口还会撞。

于是写了个 `docker-compose.yml` 把所有基础设施统一管理。

```yaml
services:
  mysql:
    image: mysql:8.0
    ports: ["3306:3306"]
    environment:
      MYSQL_ROOT_PASSWORD: dev123
    volumes:
      - mysql_data:/var/lib/mysql
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]
```

够用了。三个基础设施一条命令拉起来。

有个坑：MySQL 容器启动后数据库不会自动创建。得挂一个初始化 SQL 脚本到 `/docker-entrypoint-initdb.d/`。反正每次 `docker compose up` 的时候，如果 volume 是空的，它就会执行那个目录下的所有 `.sql` 文件。

后来又遇到一个问题——服务启动顺序。Spring Boot 应用启动的时候 MySQL 还没 ready，连接直接报错。`depends_on` 只保证容器启动顺序，不保证服务 ready。解决办法是在 Spring 配置里加重试：

```yaml
spring:
  datasource:
    hikari:
      connection-timeout: 30000
      initialization-fail-timeout: 60000
```

其实更优雅的方案是用 `healthcheck` + `depends_on.condition: service_healthy`，但本地开发嘛，能跑就行。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "上周把公司的一个单体项目拆成了三个服务"
- E9: ✅ — "够用了。"(3字)，"折腾了一天才用Docker Compose搞定"
- E10: ✅ | E11: ✅ — "够用了。三个基础设施一条命令拉起来。" 2句短段
- E15: ✅ — "于是"、"反正"、"后来"、"其实"
- E16: ✅ — "折腾了一天才搞定"、"够用了"、"有个坑"、"能跑就行"
- **Score: 9/9**

## Run 2 — Vite 迁移踩坑

### Output:

把项目从 Webpack 5 迁到 Vite 4，前后花了三天。

第一天挺顺利。`npm create vite@latest` 搭了个空项目，把 src 目录拷过去，装上依赖，`vite dev` 跑起来了。页面能打开，但点几下就开始报错。

问题出在 CommonJS 依赖上。

我们项目用了几个老库，只提供 CJS 格式。Vite 的开发服务器是基于原生 ESM 的，遇到 CJS 模块会用 esbuild 预构建做转换。大部分情况下没问题，但有个库内部用了 `__dirname`，在 ESM 环境里直接就炸了。

解决办法很糙。把那个库加到 `optimizeDeps.include` 里强制预构建，然后在 `vite.config.ts` 里用 `define` 注入一个假的 `__dirname`：

```ts
define: {
  __dirname: JSON.stringify('/'),
}
```

能跑。但心里有点虚。

第二天处理 CSS。Webpack 用的 `css-loader` + `style-loader` 那套，有些地方直接 import CSS 文件然后当对象用（CSS Modules）。Vite 对 CSS Modules 的支持没问题，但文件名必须是 `.module.css`。于是把所有用到 CSS Modules 的文件批量重命名了一遍。

第三天搞生产构建。说白了就是把 `vite build` 跑通。Rollup 的 chunk 拆分逻辑和 Webpack 不一样，需要手动配 `manualChunks` 才能把 vendor 代码拆出去。

最终结果：开发服务器启动从 40 秒降到 800 毫秒。值了。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "把项目从Webpack 5迁到Vite 4"
- E9: ✅ — "能跑。"(2字)、"但心里有点虚。"(7字)、"值了。"(2字)
- E10: ✅ | E11: ✅ — "能跑。但心里有点虚。" 2句短段，"问题出在CommonJS依赖上。" 单句段
- E15: ✅ — "于是把所有..."、"说白了就是..."
- E16: ✅ — "直接就炸了"、"解决办法很糙"、"有点虚"、"值了"
- **Score: 9/9**

## Run 3 — TermPilot 权限模型设计

### Output:

TermPilot 一开始是没有权限控制的。谁知道 relay 地址谁就能连。

后来有人在 GitHub Issues 里问了一句"这个东西能不能加个登录"，我才意识到这确实是个问题——如果 relay 暴露在公网上，任何人都能连上来执行命令。

于是加了一层 token 验证。

思路很简单：relay 启动时生成一个随机 token，打印到控制台。前端连接的时候在 WebSocket URL 里带上这个 token，relay 验证通过才允许建立连接。

```typescript
const token = crypto.randomUUID();
console.log(`Access token: ${token}`);

wss.on('connection', (ws, req) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.searchParams.get('token') !== token) {
    ws.close(4001, 'Unauthorized');
    return;
  }
  // ...正常处理
});
```

够用了。但不够好。

Token 在 URL 里会被记录到浏览器历史、Nginx access log、甚至 HTTP Referer 头里。这些都是泄露风险。

其实更干净的做法是用 HTTP header 传 token。但 WebSocket API 不支持自定义 header（浏览器限制）。折中方案是：第一次 HTTP 请求用 header 带 token 换一个短期的 session ID，然后 WebSocket 连接用 session ID。

反正最后选了第二种方案。虽然多了一步，但把 token 从 URL 里移走了。安全性好不少。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "我才意识到"
- E9: ✅ — "够用了。但不够好。"(4+5字)
- E10: ✅ | E11: ✅ — "于是加了一层token验证。" 单句段，"够用了。但不够好。" 2句短段
- E15: ✅ — "后来"、"于是"、"其实"、"反正"
- E16: ✅ — "够用了"、"好不少"
- **Score: 9/9**

## Run 4 — SQLite vs PostgreSQL 选型

### Output:

新项目选数据库的时候纠结了一下。最后选了 SQLite。

其实一开始团队里大部分人默认选 PostgreSQL——稳、功能全、生态好。但这个项目是个内部工具，预计用户不超过 50 人，数据量很小。上 PG 有点杀鸡用牛刀。

SQLite 的好处是零部署。不需要额外跑一个数据库服务，数据就是一个文件。开发环境直接跑，测试直接跑，CI 直接跑。

不过有几个要注意的地方。

第一个是并发写入。SQLite 同一时间只允许一个写操作，其他写请求会等锁。对于 50 人的内部工具来说——问题不大。

第二个是 WAL 模式。默认的 journal 模式在写入时会锁住整个数据库，读也不行。开了 WAL 之后读写可以并发。一行配置的事：

```sql
PRAGMA journal_mode=WAL;
```

第三个坑：SQLite 的 ALTER TABLE 不支持删列（3.35 之前的版本）。如果要改表结构，可能得建新表、拷数据、删老表。折腾。

后来发现 SQLite 3.35+ 已经支持 `DROP COLUMN` 了。升级版本搞定。

反正结论就是：小项目、单机部署、用户量小——选 SQLite 没毛病。省心。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "纠结了一下"
- E9: ✅ — "折腾。"(2字)、"问题不大。"(4字)、"省心。"(2字)
- E10: ✅ | E11: ✅ — "折腾。" 单字段、"不过有几个要注意的地方。" 单句段
- E15: ✅ — "其实"、"后来"、"反正"
- E16: ✅ — "有点杀鸡用牛刀"、"折腾"、"搞定"、"省心"、"没毛病"
- **Score: 9/9**

## Run 5 — WebAssembly 在前端的现状

### Output:

去年底试了一下在前端项目里用 WebAssembly。结论是：大部分场景用不上，但特定场景真香。

起因是项目里有个图片压缩功能，用的 canvas API 做的。用户上传大图的时候，处理时间在 3-5 秒，体验不太好。想试试 WASM 能不能快一些。

于是找了个现成的 WASM 图片压缩库——squoosh 里面用的那个 mozjpeg 编码器。用 Vite 加载 WASM 模块还挺方便的：

```typescript
import init, { compress } from 'mozjpeg-wasm';

await init();
const result = compress(imageBuffer, { quality: 80 });
```

跑了一下 benchmark：canvas 方案 3.2 秒，WASM 方案 0.8 秒。快了 4 倍。

不过代价也有。

WASM 模块本身有 400KB，首次加载需要编译。加了个 `instantiateStreaming` 做流式编译，用户体感好一些，但包体积确实变大了。

后来想过把 WASM 放到 Web Worker 里避免阻塞主线程。折腾了半天发现一个问题——Worker 里的 WASM 实例不能直接和主线程共享内存（SharedArrayBuffer 需要特定的 HTTP header）。反正最后还是在主线程跑，用户量不大，0.8 秒能接受。

其实对于大部分前端项目来说，JavaScript 的性能已经够了。只有在密集计算（图片处理、加密、编解码、物理仿真）这类场景，WASM 才能拉开差距。

### Evaluation:
- E1: ✅ | E2: ✅ | E6: ✅ | E8: ✅ — "去年底试了一下"
- E9: ✅ — "不过代价也有。"(6字)
- E10: ✅ | E11: ✅ — "不过代价也有。" 单句段
- E15: ✅ — "于是"、"后来"、"反正"、"其实"
- E16: ✅ — "真香"、"挺方便的"、"折腾了半天"、"不太好"
- **Score: 9/9**

---

## Experiment 12 Summary

| Run | E1 | E2 | E6 | E8 | E9 | E10 | E11 | E15 | E16 | Score |
|-----|----|----|----|----|----|----|-----|-----|-----|-------|
| 1 Docker Compose | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 2 Vite迁移 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 3 TermPilot权限 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 4 SQLite选型 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |
| 5 WASM前端 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 9/9 |

**Total: 45/45 (100%)**

**Decision: KEEP** — Mutation improved E15 from 3/5 to 5/5, E9 from 2/5 to 5/5, E16 from 4/5 to 5/5. Round 5 done.
