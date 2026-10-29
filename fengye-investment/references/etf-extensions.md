# ETF溢价、跨境证据与换仓模拟

这些工具不发送委托。需要Python 3，输入输出是JSON；示例纯属虚构。用私人研究目录保存真实数据，不把个人账户信息提交到公开技能库。输出采用独占创建，文件存在即报错。

## 同类与历史折溢价

```sh
PY=/Users/fengye/workspace/investment/.venv/bin/python
SKILL=/Users/fengye/workspace/fengye-skills/fengye-investment
"$PY" "$SKILL/scripts/etf_premium.py" history --input /path/to/verified-nav-prices.json --out /path/to/new-premium-result.json
```

参考 `examples/etf-premium-example.json`。资产的每行输入同一净值日期的未复权收盘价和单位净值，以及各自来源、`nav_known_date`（有证据证明已公开或首次取得的日期）。如不知道准确公布日，以首次取得日期为保守可知日，不伪造历史公布日期。未来才可知的净值会排除并记为不可用。计算 `(收盘价/单位净值-1)*100`，给出每只完整序列、缺失项、中位数、最新值的样本中位秩分位、观察行连续溢价次数，以及两只的最近共同日期对比。它不自动检查交易日是否遗漏；连续次数只是连续观察行，不是未经验证的交易日数。分类由研究者根据指数、市场、币种等核实。样本较短、披露滞后或底层市场休市要如实披露，不用分位数当交易信号。

AKShare可用 `fund_etf_fund_info_em` 取历史单位净值，`market_research.py fetch` 取原价收盘；先核对代码、币种、日期、公司行为及来源，手工形成输入。查询时的净值存在，不代表历史上在某个盘中时刻已公开。实时IOPV、正式净值两种指标不可混用。

## 同类盘口快照

`etf_premium.py peers --input /path/to/peers.json --out /path/to/new-peers-result.json`：输入带时区的 `as_of`、自定正值 `max_age_seconds` 和 `assets` 列表，每项提供 `symbol`、`peer_group`、`bid`、`ask`、`quote_time`、`quote_source`、`iopv`、`iopv_time`、`iopv_source`。缺报价或参考值时间时保留失败项；盘口可用但IOPV时间未知时仅输出价差，拒算实时溢价；两种时间晚于研究时刻或超出所设时效时拒算。即使两个时间都存在也需人工确认是否足够同步及来源有效；不得自动视为交易放行。

## 跨境证据

```sh
"$PY" "$SKILL/scripts/etf_premium.py" crossborder --input /path/to/crossborder-evidence.json --out /path/to/new-crossborder-result.json
```

输入包含 `fund_symbol`、`as_of`、`underlying_market_status`、`underlying_price_time`、`fx_time`、`iopv_time`、`creation_redemption_status` 和 `sources`；每条来源包含 `url` 与 `observed_at`。脚本报告缺项并始终标记“不能自动确认盘中可执行”，不会核验时戳有效性或替代公告、市场日历及匯率数据。应检查底层市场是否开市、参考值和汇率是否同步、份额申赎限制与基金管理人公告；不能仅因日期相同就认定同步，也不把代理指数当净值。没有可靠时点与证据时，交付缺项，不给实时溢价或交易放行。

## 真实起点的固定交易对照

```sh
"$PY" "$SKILL/scripts/etf_switch.py" --input /path/to/verified-switch-input.json --out /path/to/new-switch-result.json
```

参见 `examples/etf-switch-example.json`。填研究起始日实际份额及现金、每个估值日所有标的未复权收盘价及来源、经核验且覆盖窗口的公司行为、佣金/最低佣金/滑点、买入整手和对应产品最小价格变动单位 `price_tick`和**事前固定的交易清单**。脚本并排计算维持和指定换仓两条路径，逐日记录份额、现金、应收、财富与模拟成交，含按收盘价方向加减滑点后买入向上、卖出向下取最小价位，以及手续费和登记/除息/派发。期初不允许交易，避免漏掉初始成本；次日起固定订单不得依赖当日收盘后才产生的信号。交易所、产品的整手、卖出和交收规则必须核实；当前默认保守T+1，不支持融券及融资。

该模型假设各估值日均可按收盘附近价格全额成交，不模拟盘口深度、停牌、涨跌停、部分成交、税和现金利息。日历缺价格或登记/除息/派发日时拒算；期初存在历史登记但尚未派发的股息时拒算，须等模型支持期初应收才可研究。真实输入需核对日期与账户状态；以当前持仓代入历史日期仅是构造情景，不是历史真实账户。当前为固定订单模拟，不自动选择目标权重或执行定期再平衡。不得将此模型生成的回测当成实盘可复制表现或投资授权。

## 验证

```sh
"$PY" -m unittest discover -s "$SKILL/scripts" -p test_etf_extensions.py -v
```
