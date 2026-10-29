# 可执行的行情、技术、风险与ETF对比

用本流程回答“最近怎样走”“两只是否真正分散”“分散改善多大”。脚本位于 `scripts/market_research.py`，需要Python、AKShare、pandas、numpy；优先用私人投资工作区现有环境。原始数据和结果写入私人目录，不写入公开技能库。

## 1. 获取数据与审读公司行为

从技能根目录执行，另为每次研究设独立目录：

```bash
INVEST_PY=/Users/fengye/workspace/investment/.venv/bin/python
RUN_DIR=/tmp/investment-study-example
"$INVEST_PY" scripts/market_research.py fetch \
  --codes sh515080,sh512890 --kind etf \
  --start 2025-10-27 --end 2026-10-29 --out "$RUN_DIR/market.json"
"$INVEST_PY" scripts/market_research.py prepare-actions \
  --bundle "$RUN_DIR/market.json" --out "$RUN_DIR/actions-draft.json"
```

这两个日期只是可替换的调用示例，实际研究根据问题确定日期。ETF取腾讯原价日线、东方财富指定代码盘口与基金派息快照，结果逐资产保存成功/失败、AKShare版本、查询时点、源报价时点及实际覆盖日期。个股可用 `--kind stock` 取日线，财报与估值走个股模块。工具当前只适配沪深显式代码，不假装自动覆盖所有市场。

检查 `history_status`、`last_date`、`failures`。接口失败保留原错误类别；历史成功而盘口失败时仍可做历史研究，不能说取得最新盘口。盘后报价是收盘/源更新快照，不能当此刻可成交价。

派息草稿的 `reviewed` 默认false，不能直接算总回报。逐笔核对记录与公告、检查区间内拆分/折算，另存审读版，例如：

```json
{
  "sh515080": {
    "reviewed": true,
    "source": "填实际接口、快照路径及核对公告，不使用此占位文本",
    "coverage_start": "2025-10-27",
    "coverage_end": "2026-10-29",
    "notes": "写核对范围、遗漏风险；不是脚本自动通过",
    "events": [
      {"type": "dividend", "record_date": "2026-09-15", "ex_date": "2026-09-16", "pay_date": "2026-09-21", "cash_per_unit": 0.015}
    ]
  }
}
```

上面只展示**一条事件的格式，并非完整清单，不可直接拿来算全年回报**。拆分事件用 `{"type":"split","effective_date":"YYYY-MM-DD","ratio":2}` 表示一份变两份。来源不能只填“已验证”；覆盖范围内未取得完整行为时保留false，或明确只分析裸价。空派息表不能推断没有拆分。

## 2. 执行计算

```bash
"$INVEST_PY" scripts/market_research.py analyze \
  --bundle "$RUN_DIR/market.json" --actions "$RUN_DIR/actions-reviewed.json" \
  --weights 0.6,0.4 --chart --out "$RUN_DIR/results-01"
```

不提供 `--actions` 也可计算技术指标，但含现金总回报、组合回撤和收益相关性会显示不可计算。工具不把前复权价格比默认为总回报。输出目录必须为空或不存在；旧快照/报告不会被覆盖。

产物包括 `analysis.json`、`report.md`、输入副本、各资产逐日股份/现金/应收/财富CSV，以及指定权重的组合财富CSV。记录行情及公司行为各自的SHA-256，改变事件清单会改变可追溯输入。

`--chart`需要matplotlib，额外输出近120交易日原价OHLC蜡烛、MA20/60与成交量PNG。缺依赖/字段会在JSON保留绘图失败，不能假称图已生成；图明确标注未复权，遇分红/拆分跳空结合事件核对，不当总回报图。

### 实际算什么

|计算|定义与输入|如何用于判断|
|---|---|---|
|日线结构|MA20/60/120、均线5个交易日前后斜率、5/20/60期裸价变动、近20收盘高低、量比|例如价格>MA20>MA60且均线向上支持趋势描述；缠绕则不称明确趋势。除息/拆分附近先核对价位口径；收盘区间不是盘中阻力保证|
|周线结构|日线按W-FRI聚合，仅纳入周五标签不晚于数据末日的周，周MA20|保守排除尚未完成的日历周；未接交易日历时节假日提前结束的周可能漏计，不能据此判断真实交易周未完成|
|单只总回报|首日收盘买一份，除息按登记份额记应收，派发转现金，拆分改份额；期末财富/期初财富−1|包含留存现金但不自动复投，税前零成本，不是含税实盘账本；账本可逐行对照|
|年化/波动|CAGR按实际日数365.25；日简单收益样本标准差×sqrt(252)|短样本年化容易误导，应同列实际累计回报、起止日和样本数|
|最大回撤|每日财富/截至当日最高财富−1的最小值，并报峰、谷及恢复日|比较同窗口并解释峰谷可能不同；收盘回撤不是盘中或未来亏损上限|
|分散|同日财富收益Pearson、滚动60日相关、第一只下跌日的条件相关与样本数|不能只报一个相关系数；结合行业与重叠，不把正相关小于1称为对冲|
|指定权重组合|各资产财富归一化后按初始资金权重加总；不再平衡|这是零成本碎份额的持有对照。改变权重不是“最优”；现实换仓、整手与成本还须独立策略回测|
|盘口成本|最新价或卖一/所报IOPV−1、价差/买卖中间价|IOPV独立时间未知时只报算术值；`executable_premium_verified`为false，不给交易放行结论|

比较路径日期不同会拒绝静默删除日期/填充未知价格。缺交易日要先辨别停牌、缺源、交易所假日，建好估值日历再比。脚本没有自动交易、择时优化、税费、利息、整手、未成交或定期再平衡引擎，不把这些未实现能力写进已验证结果。

## 3. 持仓重叠与产品差异

按同一披露日期导出**占基金净值的小数权重**，例如：

```json
{
  "fund-a": {"as_of":"2026-06-30","scope":"top10","source":"虚构格式示例",
    "holdings":[{"code":"security-x","weight":0.10,"sector":"bank"}]},
  "fund-b": {"as_of":"2026-06-30","scope":"full","source":"虚构格式示例",
    "holdings":[{"code":"security-x","weight":0.20,"sector":"bank"},{"code":"security-y","weight":0.80,"sector":"other"}]}
}
```

```bash
"$INVEST_PY" scripts/market_research.py holdings \
  --profiles "$RUN_DIR/profiles.json" --out "$RUN_DIR/holdings-comparison.json"
```

共同持仓重叠为每个相同证券的 `min(weight_a,weight_b)` 之和；例中仅能确认至少10%净值重叠。脚本保留披露日期、覆盖率、行业权重下界和证券集中度HHI下界，不把前十重仓归一到100%，也不把异期披露说成当前完整重叠。完整ETF比较还要手工核对：

- 指数纳入、加权和调样规则，行业/个股上限与实际暴露；“低波动”是规则，不等于最大回撤一定小。
- 管理托管费用与实际跟踪差异。指数总回报和基金同口径净值对齐后，跟踪差异看累计收益差，跟踪误差看日收益差标准差年化；价格溢价变化不能冒充基金跟踪误差。
- 现金分配率 = 同窗口已实施每份现金/同一参考日价格；指数股息率、基金现金派息率和总收益三者分开。
- 费用差、银行等集中风险、现金到账偏好和调整成本，是否足以抵消回测改善。结论可以是维持；不能为了给组合凑第二只产品而推荐。

## 4. 把计算变成研究结论

先交代截至日期与缺项，再围绕原问题引用计算证据：趋势有何变化、产品风险是否不同、加入后改善多大、付出什么代价。提出维持/调整/暂缓及会改变结论的事实。若尚未核对持仓/估值，只交付技术或组合证据，不包装成完整买入研究。

将报告、输入、账本、事件核对说明与脚本版本保存在同一个私人研究目录，通过现有 `投资研究索引.md` 连接。方向调整用有日期的新条目链接旧结论；建议、采纳和成交分开。

## 实现与上游对应

`stock-correlation`的整体/滚动/下跌条件分析被实现为`compare_paths`，此处采用财富的日简单收益而非其log收益，原因是组合与留存股息口径统一；`etf-premium`和`stock-liquidity`的报价/净值/价差拆解落实为`quote_diagnostics`，排除昨收回退与异时报价放行；`technical-analyst`的量价/均线/日周结构落实为`technical`，不做未经统计检验的情景概率。算法为本地独立实现，来源详见 [upstream-methods.md](upstream-methods.md)。

离线经济不变量测试：

```bash
"$INVEST_PY" -m unittest discover -s scripts -p test_market_research.py -v
```
