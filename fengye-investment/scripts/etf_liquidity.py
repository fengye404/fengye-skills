#!/usr/bin/env python3
"""Historical ETF turnover and hypothetical order-size/cost diagnostics.

Uses actual CNY turnover, not close*volume. No impact model or trade execution.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import sys

import pandas as pd

from market_research import clean, dump, stamp


def positive(value, name, allow_zero=False):
    if isinstance(value, bool):
        raise ValueError(f"{name}不能是布尔值")
    value = float(value)
    if not math.isfinite(value) or value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name}须为有限{'非负' if allow_zero else '正'}数")
    return value


def date_index(values):
    dates = pd.DatetimeIndex(pd.to_datetime(values, errors="raise"))
    if dates.tz is not None:
        raise ValueError("交易日期使用不带时区的YYYY-MM-DD，查询时间另记")
    dates = dates.normalize()
    if dates.hasnans or dates.duplicated().any():
        raise ValueError("交易日期含无效或重复项")
    return dates.sort_values()


def observed_frame(rows):
    frame = pd.DataFrame(rows)
    if not {"date", "amount"}.issubset(frame.columns):
        raise ValueError("历史需date和实际amount；不能拿收盘×成交量冒充成交额")
    parsed = pd.to_datetime(frame.pop("date"), errors="raise").dt.normalize()
    if parsed.isna().any() or parsed.duplicated().any():
        raise ValueError("历史日期无效或重复")
    frame.index = pd.DatetimeIndex(parsed)
    if frame.index.tz is not None:
        raise ValueError("历史交易日期不能带时区")
    frame["amount"] = frame["amount"].map(lambda value: None if isinstance(value, bool) else value)
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce")
    if (frame["amount"].dropna() < 0).any() or frame["amount"].isin([float("inf"), float("-inf")]).any():
        raise ValueError("实际成交额不得为负数或无穷")
    return frame.sort_index()


def window_stats(frame, window, calendar=None, statuses=None, order_amount=None):
    statuses = statuses or {}
    dates = calendar if calendar is not None else frame.index
    if not len(dates):
        raise ValueError("没有可用日期")
    dates = dates[-window:]
    sample = frame.reindex(dates)
    amount = sample["amount"].copy()
    states = []
    for date in dates:
        key = str(date.date())
        explicit = statuses.get(key)
        if explicit not in (None, "trading", "suspended", "missing", "unknown"):
            raise ValueError(f"未知交易状态：{explicit}")
        value = amount.loc[date]
        if explicit == "suspended":
            if pd.notna(value) and value != 0:
                raise ValueError("声明停牌但成交额为正，先核对日期和来源")
            amount.loc[date] = 0.0
            states.append("suspended")
        elif explicit in ("missing", "unknown"):
            amount.loc[date] = float("nan")
            states.append("missing")
        elif pd.isna(value):
            states.append("missing")
        elif value == 0:
            states.append("reported_zero")
        else:
            states.append("positive")
    known = amount.dropna()
    active = amount[[state != "suspended" for state in states]].dropna()
    missing = states.count("missing")
    # Means retain actual reported zeros. Unknown sessions never become zeros.
    mean = known.mean() if len(known) else None
    complete_window = len(dates) == window and not missing
    result = {
        "requested_sessions": window, "sample_sessions": len(dates),
        "start": str(dates[0].date()), "end": str(dates[-1].date()),
        "calendar_known": calendar is not None,
        "calendar_basis": "explicit expected exchange sessions" if calendar is not None else "observed quote dates only; cannot detect absent sessions",
        "numeric_rows_complete": complete_window,
        "complete_expected_sessions": complete_window and calendar is not None,
        "calendar_coverage_warning": "未提供交易日历；满观察行不证明交易日无遗漏" if calendar is None else None,
        "known_amount_days": len(known), "missing_or_unknown_days": missing,
        "reported_zero_amount_days": states.count("reported_zero"),
        "declared_suspended_days": states.count("suspended"),
        "mean_amount_known_cny": mean,
        "median_amount_known_cny": known.median() if len(known) else None,
        "p10_amount_known_cny": known.quantile(0.1) if len(known) else None,
        "min_amount_known_cny": known.min() if len(known) else None,
        "mean_amount_active_known_cny": active.mean() if len(active) else None,
        "zero_treatment": "reported zero retained as zero; input-declared suspension separately counted and zero for venue-session capacity; missing stays unknown",
        "thin_sample_warning": None if complete_window else "样本不足或有缺项；均值仅基于已知金额，不代表完整请求窗口",
    }
    if order_amount is not None:
        median = result["median_amount_known_cny"]
        p10 = result["p10_amount_known_cny"]
        result["hypothetical_order"] = {
            "amount_cny": order_amount,
            "pct_of_mean_known_turnover": order_amount / mean * 100 if mean and mean > 0 else None,
            "pct_of_median_known_turnover": order_amount / median * 100 if median and median > 0 else None,
            "pct_of_p10_known_turnover": order_amount / p10 * 100 if p10 and p10 > 0 else None,
            "denominator_is_complete_requested_window": complete_window and calendar is not None,
            "limitation": "这是日成交额参与率，不是盘口可成交规模或冲击成本预测；不能保证买一卖一成交",
        }
    return clean(result)


def quote_cost(quote, amount, commission_rate=None, min_commission=0, side="buy"):
    result = {"hypothetical_order_cny": amount, "side": side,
              "quote_time": quote.get("更新时间") if quote else None,
              "reference_only": True, "quote_and_depth_freshness_verified": False,
              "market_impact_modelled": False, "taxes_and_other_fees_modelled": False}
    legs = 2 if side == "roundtrip" else 1
    commission = max(amount * commission_rate, min_commission) * legs if commission_rate is not None else None
    result["commission_reference_cny"] = commission
    try:
        bid, ask = positive(quote["买一"], "bid"), positive(quote["卖一"], "ask")
        if not all(math.isfinite(v) and v > 0 for v in (bid, ask)) or ask < bid:
            raise ValueError("无效买卖价")
        mid = (ask + bid) / 2
        half_spread = (ask - bid) / (2 * mid)
        spread_cost = amount * half_spread * legs
        result.update(bid=bid, ask=ask, spread_pct=(ask-bid)/mid*100,
                      half_spread_per_leg_pct=half_spread*100,
                      midpoint_spread_reference_cny=spread_cost,
                      commission_plus_spread_reference_cny=commission+spread_cost if commission is not None else None)
    except (KeyError, TypeError, ValueError):
        result["spread_unavailable"] = "盘口缺失/无效；不拿历史收盘价制造价差"
    result["assumptions"] = "相同名义金额、每腿从中间价到对手价的半价差；往返仅为同盘口假设。实际买卖价变化、挂单量、整手、未成交、额外滑点和税费未模拟；佣金费率/最低额由调用者显式给定。"
    return clean(result)


def analyze(bundle, windows, amount_unit, order_amount=None, calendar=None, statuses=None,
            commission_rate=None, min_commission=0, side="buy"):
    if amount_unit != "CNY":
        raise ValueError("须明确成交额amount单位为CNY；不能猜万元/元转换")
    if not windows or any(not isinstance(w, int) or w <= 0 for w in windows):
        raise ValueError("窗口必须为正整数")
    if order_amount is not None:
        order_amount = positive(order_amount, "order amount")
    if commission_rate is not None:
        commission_rate = positive(commission_rate, "commission rate", True)
    min_commission = positive(min_commission, "minimum commission", True)
    if side not in ("buy", "sell", "roundtrip"):
        raise ValueError("side须为buy/sell/roundtrip")
    cutoff = pd.Timestamp(bundle["requested_end"]).normalize()
    calendar = date_index(calendar) if calendar is not None else None
    if calendar is not None:
        calendar = calendar[calendar <= cutoff]
    result = {"schema": "etf-liquidity-v1", "generated_at": stamp(),
              "queried_at": bundle.get("queried_at"), "requested_end": bundle["requested_end"],
              "amount_unit": amount_unit, "assets": {}, "fetch_failures": bundle.get("failures", []),
              "scope": "历史成交/假设订单/报价成本参考；不做流动性评分、不模拟成交或申赎、不实现平方根冲击模型"}
    for code, asset in bundle["assets"].items():
        row = {"source": asset.get("history_interface"), "history_status": asset.get("history_status")}
        try:
            if asset.get("history_status") != "ok":
                raise ValueError(asset.get("history_error", "历史不可用"))
            frame = observed_frame(asset["history"])
            frame = frame.loc[:cutoff]
            if frame.empty:
                raise ValueError("截止日前没有历史")
            row["actual_last_date"] = str(frame.index[-1].date())
            row["window_stats"] = [window_stats(frame, w, calendar, (statuses or {}).get(code), order_amount) for w in windows]
            if order_amount is not None:
                row["cost_reference"] = quote_cost(asset.get("quote"), order_amount, commission_rate, min_commission, side)
        except (ValueError, KeyError, TypeError) as exc:
            row["error"] = str(exc)
        result["assets"][code] = clean(row)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, help="market_research fetch输出")
    parser.add_argument("--amount-unit", required=True, choices=["CNY"], help="先核验原始amount单位，显式声明")
    parser.add_argument("--windows", default="20,60")
    parser.add_argument("--order-amount", type=float, help="对每只资产分别考察的假设人民币订单，不是加总配置")
    parser.add_argument("--commission-rate", type=float, help="显式费率，如万一为0.0001；不提供则未知")
    parser.add_argument("--minimum-commission", type=float, default=0)
    parser.add_argument("--side", choices=["buy", "sell", "roundtrip"], default="buy")
    parser.add_argument("--calendar", help="JSON交易日期列表；不提供时只能识别已观察报价日")
    parser.add_argument("--statuses", help="JSON {symbol:{YYYY-MM-DD:trading/suspended/missing/unknown}}")
    parser.add_argument("--out", required=True, help="新结果目录，拒绝覆盖")
    args = parser.parse_args()
    try:
        out = Path(args.out)
        if out.exists() and any(out.iterdir()):
            raise ValueError("输出目录非空，请指定新研究目录")
        raw = Path(args.bundle).read_bytes()
        inputs = {}
        for name in ("calendar", "statuses"):
            source = getattr(args, name)
            if source:
                content = Path(source).read_bytes()
                inputs[name] = {"path": str(Path(source).resolve()), "sha256": hashlib.sha256(content).hexdigest(), "data": json.loads(content)}
        result = analyze(json.loads(raw), [int(w) for w in args.windows.split(",")], args.amount_unit,
                         args.order_amount, inputs.get("calendar", {}).get("data"), inputs.get("statuses", {}).get("data"),
                         args.commission_rate, args.minimum_commission, args.side)
        result.update(input_path=str(Path(args.bundle).resolve()), input_sha256=hashlib.sha256(raw).hexdigest(),
                      additional_inputs=inputs,
                      cost_parameters={"commission_rate": args.commission_rate, "minimum_commission": args.minimum_commission, "side": args.side})
        out.mkdir(parents=True, exist_ok=True)
        with (out / "market-input.json").open("xb") as stream:
            stream.write(raw)
        dump(out / "liquidity.json", clean(result))
        lines = ["# ETF历史流动性与订单规模", "", "金额单位：人民币元。均值保留已报告零成交，未知不补零；无交易日历时不能识别缺失交易日。", "",
                 "|标的|窗口|实际样本|均成交额|中位额|P10|零成交/停牌/缺失|订单/已知均额%|", "|---|---:|---:|---:|---:|---:|---|---:|"]
        for code, row in result["assets"].items():
            if "error" in row:
                lines.extend(["", f"- {code}失败：{row['error']}"])
                continue
            for w in row["window_stats"]:
                fmt = lambda value: "未知" if value is None else f"{value:,.4f}"
                participation = w.get("hypothetical_order", {}).get("pct_of_mean_known_turnover")
                lines.append(f"|{code}|{w['requested_sessions']}|{w['sample_sessions']}|{fmt(w['mean_amount_known_cny'])}|{fmt(w['median_amount_known_cny'])}|{fmt(w['p10_amount_known_cny'])}|{w['reported_zero_amount_days']}/{w['declared_suspended_days']}/{w['missing_or_unknown_days']}|{fmt(participation)}|")
        lines.extend(["", "订单占日成交额很小不保证能在盘口全额成交。成本参考及报价时间见JSON；无盘口不制造价差。未计底层篮子、申赎限制、额外冲击及税费，不给综合评分或买入指令。"])
        with (out / "report.md").open("x", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
        print(json.dumps({"saved": str(out), "assets": len(result["assets"])}, ensure_ascii=False))
        return 2 if all("error" in row for row in result["assets"].values()) else 0
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
