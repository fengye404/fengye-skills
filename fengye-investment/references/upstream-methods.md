# 上游方法与本地适配

用于维护本技能、解释方法来源与继续深化研究。2026-10-29查阅相关SKILL正文后提炼，以下是方法吸收与取舍，不宣称上游脚本已在A股实测。本技能按本地数据和用户目标重写流程，不要求安装整个上游仓库。

| 模块 | 参考上游 | 吸收的方法 | 本地适配与排除 |
|---|---|---|---|
| 策略验证 | [tradermonty/backtest-expert](https://github.com/tradermonty/claude-trading-skills/blob/main/skills/backtest-expert/SKILL.md) | 事前明确假设和交易规则、成本压力、参数邻域、分行情区间、样本外检验 | 采用原价和公司行为记账；低频配置不硬套30笔或5年合格线；自动评分与DEPLOY不代表授权或收益可靠 |
| 技术分析 | [tradermonty/technical-analyst](https://github.com/tradermonty/claude-trading-skills/blob/main/skills/technical-analyst/SKILL.md) | 日周趋势、均线、量价、关键位置、情景与失效条件 | 从已核验数据计算和绘图；不要求用户先提供周线图片，不凭形态编概率，不替代基本面 |
| 高息个股筛选 | [tradermonty/value-dividend-screener](https://github.com/tradermonty/claude-trading-skills/blob/a351386bd6736cbba7b42c34e6b792c7bc31363b/skills/value-dividend-screener/SKILL.md) | 先粗筛再逐公司验证；派息增长、收入/EPS趋势、派息率、FCF覆盖和财务质量 | 使用AKShare与公告；不要求FINVIZ/FMP密钥；不照搬PE<20、PB<2、股息>3%及合成评分；金融企业另用行业指标 |
| ETF交易质量 | [himself65/etf-premium](https://github.com/himself65/finance-skills/blob/main/plugins/market-analysis/skills/etf-premium/SKILL.md) | 单只快照、同类对比、溢价来源与价差比较、跨境时差解释 | 价格/IOPV保留各自时间及有效性；不静默回退昨收，不把折价自动视作便宜，不照搬美股分档阈值 |
| 组合分散 | [himself65/stock-correlation](https://github.com/himself65/finance-skills/blob/main/plugins/market-analysis/skills/stock-correlation/SKILL.md) | 收益相关性、滚动窗口、分行情相关性、行业聚类思路 | 核对含分红口径、交易日与样本量，联同持仓重叠和回撤判断；不用价格水平相关性冒充收益相关性 |
| 流动性 | [himself65/stock-liquidity](https://github.com/himself65/finance-skills/blob/main/plugins/market-analysis/skills/stock-liquidity/SKILL.md) | 买卖价差、成交额、换手、订单规模相对日成交、冲击成本情景 | 用本地盘口与单位；模型估计不当实际成交；不把一次买入加卖出机械算作两倍完整价差 |
| 公司估值 | [himself65/company-valuation](https://github.com/himself65/finance-skills/blob/44443a08e6fdc6e7fd0df89e44ef74ef0cd4f1c4/plugins/market-analysis/skills/company-valuation/SKILL.md) | 按行业选DCF/可比/分部、企业价值到股权桥接、折现率与增长敏感性、情景 | 采用匹配币种市场的参数，不抄美债4.5%等默认值；修正前瞻倍数与TTM EPS混配、营运资本绝对值及固定退出倍数；不机械混合模型价格 |
| 同业估值 | [Anthropic/comps-analysis](https://github.com/anthropics/financial-services/blob/bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d/plugins/vertical-plugins/financial-analysis/skills/comps-analysis/SKILL.md) | 解释同业选择、统一经营与估值口径、离群值与统计分布、输入来源及可复算公式 | 用实际可用的AKShare/原始财报；不假设有付费MCP，不强制Excel、固定排版或逐阶段让用户批准 |
| 财报复盘 | [Anthropic/earnings-analysis](https://github.com/anthropics/financial-services/blob/bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d/plugins/vertical-plugins/equity-research/skills/earnings-analysis/SKILL.md) | 新旧结果与指引对比、分部/利润率/运营指标、修订假设及论点影响，逐项来源 | 无一致预期就不编超预期；使用A股累计/单季口径；不强制8–12页、图数、SEC表格或“最新必须三个月内” |
| 研究方向与决策沉淀 | [Anthropic/thesis-tracker](https://github.com/anthropics/financial-services/blob/ef165e4160f295cbe44b7797f434ddf11dbc36d8/plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md) | 可证伪论点、依据记分表、更新日志、正反证据和后续事件 | 私人中文Markdown保留日期、旧判断与状态；可兼容Obsidian；不把建议动作自动升级为采纳或成交 |

补充参考 [a-share-data](https://github.com/shouldnotappearcalm/a-share-skill/blob/main/a-share-data/SKILL.md) 的数据/公告日/缓存与缺失状态设计；仅借时间与来源区分，不默认其脚本已适配ETF。其上游路径调整时从仓库树核对实际文件，不用失效链接猜内容。

tradermonty的 `data-quality-checker` 是文稿日期、单位、比例等检查，不是价格、复权或公司行为审计；不以文稿检查通过声称数据可靠。

新借鉴规则时，先读具体正文和相关实现，核对其假设及适用市场，再把能改变分析质量的部分写入对应参考。保留出处；若直接复制或改写上游代码/较长原文，先核对许可证并保留要求的声明。本版为自写方法提炼，不内嵌上游脚本，也不把高星数当有效性证明。
