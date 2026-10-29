#!/usr/bin/env python3
"""AKShare snapshots and reproducible ETF/stock market diagnostics; no orders.

Methods are independently implemented. See references/upstream-methods.md for
the correlation, liquidity and technical-analysis workflows that informed them.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False))


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (dt.date, dt.datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def symbol(text):
    if not re.fullmatch(r"(?:sh|sz)\d{6}", text):
        raise ValueError(f"本工具仅支持显式市场代码sh/sz+六位数字：{text}")
    return text


def history_frame(rows):
    frame = pd.DataFrame(rows)
    required = {"date", "close"}
    if not required.issubset(frame.columns):
        raise ValueError("历史数据缺date/close")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    if frame["date"].duplicated().any():
        raise ValueError("历史日期重复")
    frame = frame.sort_values("date").set_index("date")
    frame["close"] = pd.to_numeric(frame["close"], errors="raise")
    if len(frame) < 2 or not np.isfinite(frame["close"]).all() or (frame["close"] <= 0).any():
        raise ValueError("至少需要两个有效正收盘价")
    return frame


def metrics(wealth):
    wealth = wealth.astype(float)
    if len(wealth) < 2 or not np.isfinite(wealth).all() or (wealth <= 0).any():
        raise ValueError("资产路径需至少两点且有限、为正")
    returns = wealth.pct_change().dropna()
    dd = wealth / wealth.cummax() - 1
    trough = dd.idxmin()
    peak = wealth.loc[:trough].idxmax()
    recovery = wealth.loc[trough:][wealth.loc[trough:] >= wealth.loc[peak]]
    days = (wealth.index[-1] - wealth.index[0]).days
    return {
        "start": str(wealth.index[0].date()), "end": str(wealth.index[-1].date()),
        "observations": len(wealth), "return_observations": len(returns),
        "cumulative_return_pct": (wealth.iloc[-1] / wealth.iloc[0] - 1) * 100,
        "cagr_pct": ((wealth.iloc[-1] / wealth.iloc[0]) ** (365.25 / days) - 1) * 100 if days else None,
        "annualized_volatility_pct": returns.std(ddof=1) * np.sqrt(252) * 100 if len(returns) > 1 else None,
        "max_drawdown_pct": dd.min() * 100,
        "drawdown_peak": str(peak.date()), "drawdown_trough": str(trough.date()),
        "recovery_date": str(recovery.index[0].date()) if not recovery.empty else None,
        "frequency": "observed daily closes; 252-return annualization; CAGR calendar days",
    }


def technical(frame):
    close = frame["close"]
    out = {"basis": "raw price; dividends/splits may distort technical levels", "last_close": close.iloc[-1]}
    for window in (20, 60, 120):
        ma = close.rolling(window).mean()
        out[f"ma{window}"] = ma.iloc[-1]
        out[f"ma{window}_change_5_sessions_pct"] = (ma.iloc[-1] / ma.iloc[-6] - 1) * 100 if len(ma) >= window + 5 else None
    for n in (5, 20, 60):
        out[f"raw_price_change_{n}_sessions_pct"] = (close.iloc[-1] / close.iloc[-n-1] - 1) * 100 if len(close) > n else None
    out["last_20_close_high"] = close.tail(20).max()
    out["last_20_close_low"] = close.tail(20).min()
    complete_weeks = close.resample("W-FRI").last()
    complete_weeks = complete_weeks.loc[complete_weeks.index <= close.index[-1]]
    out["last_complete_week_label"] = str(complete_weeks.index[-1].date()) if len(complete_weeks) else None
    out["last_complete_week_close"] = complete_weeks.iloc[-1] if len(complete_weeks) else None
    out["complete_week_ma20"] = complete_weeks.rolling(20).mean().iloc[-1] if len(complete_weeks) else None
    out["week_completion_rule"] = "仅计入周五日历标签不晚于最后行情日的周；未接交易日历，节假日提前结束的交易周可能保守漏计，不据此判断该周未交易"
    if "volume" in frame:
        volume = pd.to_numeric(frame["volume"], errors="coerce")
        baseline = volume.iloc[-21:-1].mean()
        out["last_volume_vs_prior_20_mean"] = volume.iloc[-1] / baseline if len(volume) >= 21 and baseline > 0 else None
    return clean(out)


def write_chart(frame, path, code):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    required = {"open", "high", "low", "close"}
    if not required.issubset(frame.columns):
        raise ValueError("K线缺open/high/low/close")
    data = frame.tail(120)
    if not np.isfinite(data[list(required)].astype(float)).all().all():
        raise ValueError("K线OHLC含缺失，拒绝绘制可能误导的蜡烛")
    fig, (ax, volume_ax) = plt.subplots(2, 1, figsize=(12, 7), sharex=True, gridspec_kw={"height_ratios": [4, 1]})
    for i, (_, row) in enumerate(data.iterrows()):
        color = "#c03b42" if row["close"] >= row["open"] else "#238b66"
        ax.vlines(i, row["low"], row["high"], color=color, linewidth=0.8)
        body = abs(row["close"] - row["open"])
        if body:
            ax.add_patch(Rectangle((i-0.32, min(row["close"], row["open"])), 0.64, body, facecolor=color, edgecolor=color))
        else:
            ax.hlines(row["close"], i-0.32, i+0.32, color=color)
    for window, color in ((20, "#2864a5"), (60, "#bf871c")):
        values = frame["close"].rolling(window).mean().reindex(data.index)
        ax.plot(range(len(data)), values, label=f"MA{window}", color=color, linewidth=1)
    if "volume" in data:
        volume_ax.bar(range(len(data)), pd.to_numeric(data["volume"], errors="coerce"), color="#8496a8", width=0.65)
    volume_ax.set_ylabel("Volume\n(source units)")
    ticks = list(range(0, len(data), max(1, len(data)//7)))
    volume_ax.set_xticks(ticks, [data.index[i].strftime("%Y-%m-%d") for i in ticks], rotation=25, ha="right")
    ax.set_title(f"{code} | raw OHLC, last {len(data)} sessions | as of {data.index[-1].date()}")
    ax.set_ylabel("CNY / unit")
    ax.legend(loc="upper left")
    ax.grid(alpha=0.15)
    fig.text(0.01, 0.01, "Unadjusted prices: dividends/splits can create gaps. Descriptive chart; not a total-return or buy signal.", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)


def compare_holdings(profiles):
    """Weights are decimal fractions of fund NAV, not percentages or normalized top10."""
    cleaned = {}
    for code, item in profiles.items():
        if not item.get("source") or not item.get("as_of"):
            raise ValueError("持仓需source和披露as_of")
        holdings = {}
        sectors = {}
        for row in item["holdings"]:
            weight = float(row["weight"])
            if not math.isfinite(weight) or weight < 0 or weight > 1 or row["code"] in holdings:
                raise ValueError("持仓权重需0至1的小数且证券代码不重复")
            holdings[row["code"]] = weight
            if row.get("sector"):
                sectors[row["sector"]] = sectors.get(row["sector"], 0) + weight
        coverage = sum(holdings.values())
        if coverage > 1.02:
            raise ValueError("持仓超过净值102%，检查百分比单位/重复/杠杆；本计算器不处理杠杆组合")
        cleaned[code] = {"weights": holdings, "coverage_of_nav": coverage,
                         "declared_scope": item.get("scope", "unknown"), "as_of": item["as_of"],
                         "source": item["source"], "sector_weight_lower_bounds": sectors,
                         "security_hhi_lower_bound": sum(w*w for w in holdings.values())}
    pairs = []
    codes = list(cleaned)
    for i, left in enumerate(codes):
        for right in codes[i+1:]:
            a, b = cleaned[left], cleaned[right]
            overlap = sum(min(w, b["weights"].get(k, 0)) for k, w in a["weights"].items())
            pairs.append({"left": left, "right": right, "weighted_overlap_of_nav": overlap,
                          "comparable_disclosure_date": a["as_of"] == b["as_of"],
                          "interpretation": "共同证券权重min之和；披露不完整时仅为下界，不把前十重仓归一到100%，异期不可称当期完整重叠"})
    return {"assets": cleaned, "pairs": pairs}


def holdings_command(args):
    result = compare_holdings(json.loads(Path(args.profiles).read_text()))
    dump(args.out, result)
    print(json.dumps({"saved": args.out}, ensure_ascii=False))
    return 0


def ledger(frame, actions):
    """One unit bought at first close; no reinvestment, no fees/tax or trading.

    Prices and all action dates are processed on a union calendar. Dividends use
    recorded entitlements, never current shares on ex/payment day.
    """
    start, end = frame.index[0], frame.index[-1]
    if not actions.get("reviewed") or not actions.get("source"):
        raise ValueError("公司行为需reviewed=true及source；不得把未知当无事件")
    if pd.Timestamp(actions["coverage_start"]) > start or pd.Timestamp(actions["coverage_end"]) < end:
        raise ValueError("公司行为覆盖范围不足")
    records, exdates, payments, splits = {}, {}, {}, {}
    seen_events = set()
    for i, event in enumerate(actions.get("events", [])):
        signature = json.dumps(event, sort_keys=True, ensure_ascii=False)
        if signature in seen_events:
            raise ValueError("公司行为清单含完全重复事件，先排除重复来源")
        seen_events.add(signature)
        if event["type"] == "dividend":
            record, ex, pay = [pd.Timestamp(event[k]).normalize() for k in ("record_date", "ex_date", "pay_date")]
            amount = float(event["cash_per_unit"])
            if not math.isfinite(amount) or amount < 0 or not record < ex <= pay:
                raise ValueError("股息需有效金额及record_date < ex_date <= pay_date；其他市场规则须另实现")
            if record >= start and record <= end:
                if record not in frame.index or (ex <= end and ex not in frame.index):
                    raise ValueError("登记日或区间内除息日缺收盘，无法验证有权持仓/除息估值；需先补齐或另建停牌估值模型")
                records.setdefault(record, []).append((i, amount))
                exdates.setdefault(ex, []).append(i)
                payments.setdefault(pay, []).append(i)
        elif event["type"] == "split":
            date = pd.Timestamp(event["effective_date"]).normalize()
            ratio = float(event["ratio"])
            if not math.isfinite(ratio) or ratio <= 0:
                raise ValueError("拆分比例无效")
            if start < date <= end:
                splits.setdefault(date, []).append(ratio)
        else:
            raise ValueError("不支持的公司行为，不能静默忽略")
    calendar = sorted(set(frame.index) | {d for mapping in (records, exdates, payments, splits) for d in mapping if start <= d <= end})
    shares, cash, mark = 1.0, 0.0, float(frame["close"].iloc[0])
    entitled, receivables, rows = {}, {}, []
    for date in calendar:
        if date in frame.index:
            mark = float(frame.at[date, "close"])
        for ratio in splits.get(date, []):
            shares *= ratio
            if date not in frame.index:
                mark /= ratio  # change share units while carrying a suspended quote
        for i in exdates.get(date, []):
            receivables[i] = entitled[i]
        for i in payments.get(date, []):
            cash += receivables.pop(i)
        for i, amount in records.get(date, []):
            entitled[i] = shares * amount
        rows.append({"date": date, "shares": shares, "cash": cash,
                     "receivable": sum(receivables.values()), "mark": mark,
                     "wealth": shares * mark + cash + sum(receivables.values()),
                     "observed_close": date in frame.index})
    result = pd.DataFrame(rows).set_index("date")
    return result


def quote_diagnostics(row, as_of):
    def num(key):
        try:
            value = float(row.get(key))
            return value if math.isfinite(value) and value > 0 else None
        except (ValueError, TypeError):
            return None
    price, bid, ask, iopv = [num(k) for k in ("最新价", "买一", "卖一", "IOPV实时估值")]
    quoted = row.get("更新时间")
    quoted_date = str(quoted)[:10] if quoted else None
    valid_book = bool(bid and ask and bid <= ask)
    return {
        "quote_time": quoted, "requested_as_of": as_of,
        "quote_matches_requested_date": quoted_date == as_of,
        "last": price, "bid": bid, "ask": ask, "iopv": iopv,
        "iopv_time": None,
        "last_vs_reported_iopv_pct": (price / iopv - 1) * 100 if price and iopv else None,
        "ask_vs_reported_iopv_pct": (ask / iopv - 1) * 100 if valid_book and iopv else None,
        "spread_pct": (ask - bid) / ((ask + bid) / 2) * 100 if valid_book else None,
        "turnover_pct_source_value": row.get("换手率"), "amount_cny": row.get("成交额"),
        "executable_premium_verified": False,
        "limitation": "IOPV独立时间未知；报价日期相符不证明盘中即时有效，折溢价仅为所报数值的算术比较",
    }


@contextlib.contextmanager
def targeted_etf(ak, codes):
    # Patch only this function's pagination dependency in this standalone process.
    namespace = ak.fund_etf_spot_em.__globals__
    old = namespace["fetch_paginated_data"]
    def narrowed(url, params, *args, **kwargs):
        params = dict(params)
        params["fs"] = ",".join("i:" + ("1." if code.startswith("sh") else "0.") + code[2:] for code in codes)
        params["pz"] = "100"
        return old(url, params, *args, **kwargs)
    namespace["fetch_paginated_data"] = narrowed
    try:
        yield
    finally:
        namespace["fetch_paginated_data"] = old


def fetch(args):
    import akshare as ak
    if Path(args.out).exists():
        raise ValueError("快照已存在；使用新的文件/研究目录，不覆盖旧数据")
    codes = [symbol(x) for x in args.codes.split(",")]
    bundle = {"schema": 1, "queried_at": stamp(), "akshare_version": ak.__version__,
              "requested_start": args.start, "requested_end": args.end,
              "kind": args.kind, "adjustment": "raw", "assets": {}, "failures": []}
    for code in codes:  # sequential; avoids shared JS runtime initialization failures
        item = {"history_interface": "stock_zh_a_hist_tx", "history_status": "unavailable"}
        try:
            source = ak.stock_zh_a_hist_tx(symbol=code, start_date=args.start.replace("-", ""), end_date=args.end.replace("-", ""), adjust="", timeout=12)
            frame = history_frame(source.to_dict("records"))
            frame = frame.loc[args.start:args.end]
            history_frame(frame.reset_index().to_dict("records"))
            item.update(history_status="ok", history=clean(frame.reset_index().to_dict("records")),
                        first_date=str(frame.index[0].date()), last_date=str(frame.index[-1].date()))
        except Exception as exc:
            item["history_error"] = type(exc).__name__ + ": " + str(exc)[:200]
            bundle["failures"].append({"symbol": code, "stage": "history", "error": item["history_error"]})
        bundle["assets"][code] = item
        if args.kind == "etf":
            try:
                dividends = ak.fund_open_fund_info_em(symbol=code[2:], indicator="分红送配详情")
                item["dividend_snapshot"] = clean(dividends.to_dict("records"))
                item["dividend_interface"] = "fund_open_fund_info_em/分红送配详情"
                item["dividend_status"] = "returned" if len(dividends) else "empty_unknown"
            except Exception as exc:
                item["dividend_status"] = "unavailable"
                bundle["failures"].append({"symbol": code, "stage": "dividends", "error": type(exc).__name__ + ": " + str(exc)[:200]})
    if args.kind == "etf":
        try:
            with targeted_etf(ak, codes):
                spot = ak.fund_etf_spot_em()
            for code in codes:
                rows = spot.loc[spot["代码"].astype(str).str.zfill(6) == code[2:]]
                bundle["assets"][code]["quote"] = clean(rows.iloc[0].to_dict()) if not rows.empty else None
                if rows.empty:
                    bundle["failures"].append({"symbol": code, "stage": "quote", "error": "not returned"})
        except Exception as exc:
            bundle["failures"].append({"stage": "quote", "error": type(exc).__name__ + ": " + str(exc)[:200]})
    bundle["corporate_actions_status"] = "unverified; supply reviewed actions separately for total-return analysis"
    dump(args.out, clean(bundle))
    print(json.dumps({"saved": args.out, "assets": len(codes), "failures": bundle["failures"]}, ensure_ascii=False))
    return 2 if all(x["history_status"] != "ok" for x in bundle["assets"].values()) else 0


def prepare_actions(args):
    bundle = json.loads(Path(args.bundle).read_text())
    result = {}
    for code, item in bundle["assets"].items():
        events, errors = [], []
        for row in item.get("dividend_snapshot", []):
            try:
                match = re.fullmatch(r"每10份派现金([\d.]+)元", str(row["每10份分红"]).strip())
                if not match:
                    raise ValueError("未知派息文字，不能猜金额")
                events.append({"type": "dividend", "record_date": str(row["权益登记日"])[:10],
                               "ex_date": str(row["除息日"])[:10], "pay_date": str(row["分红发放日"])[:10],
                               "cash_per_unit": float(match.group(1)) / 10})
            except (KeyError, ValueError, TypeError) as exc:
                errors.append(str(exc))
        result[code] = {"reviewed": False, "source": {"interface": item.get("dividend_interface"),
                        "queried_at": bundle.get("queried_at"), "dividend_status": item.get("dividend_status")},
                        "coverage_start": bundle["requested_start"], "coverage_end": bundle["requested_end"],
                        "events": events, "parse_errors": errors,
                        "notes": "草稿：核对每份金额、登记/除息/派发日；另核对拆分/折算及其他公司行为。空派息表不证明无事件。未审读不得将reviewed改为true。"}
    dump(args.out, result)
    print(json.dumps({"saved": args.out, "reviewed": False}, ensure_ascii=False))
    return 0


def compare_paths(paths, weights=None):
    codes = list(paths)
    first_index = paths[codes[0]].index
    if any(not paths[code].index.equals(first_index) for code in codes[1:]):
        raise ValueError("日期不一致，拒绝静默删除日期或把多日收益当同日收益；先核实缺失/停牌并建立统一估值日历")
    normalized = pd.DataFrame({code: series / series.iloc[0] for code, series in paths.items()})
    returns = normalized.pct_change().dropna()
    pairs = []
    for i, left in enumerate(codes):
        for right in codes[i+1:]:
            down = returns.loc[returns[left] < 0, [left, right]]
            roll = returns[left].rolling(60).corr(returns[right])
            pairs.append({"left": left, "right": right, "observations": len(returns),
                          "pearson_simple_returns": returns[left].corr(returns[right]),
                          "downside_condition": f"{left} return < 0",
                          "downside_observations": len(down),
                          "downside_correlation": down[left].corr(down[right]) if len(down) >= 3 else None,
                          "rolling_60_last": roll.iloc[-1] if len(roll) else None,
                          "rolling_60_min": roll.min(), "rolling_60_max": roll.max(),
                          "sample_warning": "小样本相关性不稳定" if len(returns) < 60 or len(down) < 20 else None})
    out = {"basis": "daily simple returns of cash-inclusive buy-and-hold wealth", "pairs": pairs}
    portfolio = None
    if weights is not None:
        if len(weights) != len(codes) or not all(math.isfinite(w) and w >= 0 for w in weights) or not math.isclose(sum(weights), 1, abs_tol=1e-8):
            raise ValueError("权重须与资产顺序一致、非负且合计1")
        portfolio = normalized.mul(weights, axis=1).sum(axis=1)
        out.update(weights=dict(zip(codes, weights)), portfolio=metrics(portfolio),
                   portfolio_assumptions="初始资金分配、零成本、碎份额、现金零息、不再平衡；非整手账户回测，不证明当前换仓值得")
    return clean(out), portfolio


def analyze(args):
    raw = Path(args.bundle).read_bytes()
    bundle = json.loads(raw)
    if bundle.get("adjustment") != "raw":
        raise ValueError("仅接受明确raw的快照，不把未知复权价格解释成总回报")
    action_bytes = Path(args.actions).read_bytes() if args.actions else None
    actions = json.loads(action_bytes) if action_bytes else {}
    outdir = Path(args.out)
    if outdir.exists() and any(outdir.iterdir()):
        raise ValueError("输出目录非空；请为本次计算指定新目录，保留旧结果")
    outdir.mkdir(parents=True, exist_ok=True)
    result = {"generated_at": stamp(), "input_sha256": hashlib.sha256(raw).hexdigest(),
              "input_path": str(Path(args.bundle).resolve()),
              "actions_sha256": hashlib.sha256(action_bytes).hexdigest() if action_bytes else None,
              "actions_original_path": str(Path(args.actions).resolve()) if args.actions else None,
              "actions_copy": "actions-input.json" if action_bytes else None,
              "data_queried_at": bundle.get("queried_at"), "requested_end": bundle["requested_end"],
              "assets": {}, "fetch_failures": bundle.get("failures", []),
              "assumptions": "one unit bought at first close; dividends retained as cash; no fees/tax; cash zero interest; no trading",
              "limitations": ["公司行为reviewed是分析者声明，不是脚本独立审计；来源及覆盖范围应人工核验", "风险按观察到的收盘价计算，不包括盘中回撤、成交失败或全部税费"]}
    with (outdir / "market-input.json").open("xb") as stream:
        stream.write(raw)
    if action_bytes:
        with (outdir / "actions-input.json").open("xb") as stream:
            stream.write(action_bytes)
    paths = {}
    for code, item in bundle["assets"].items():
        row = {"history_status": item.get("history_status")}
        if item.get("quote"):
            row["quote"] = quote_diagnostics(item["quote"], bundle["requested_end"])
        try:
            if item.get("history_status") != "ok":
                raise ValueError(item.get("history_error", "history unavailable"))
            frame = history_frame(item["history"])
            row.update(data_end=str(frame.index[-1].date()),
                       matches_requested_end=str(frame.index[-1].date()) == bundle["requested_end"],
                       technical=technical(frame),
                       raw_price_diagnostics=metrics(frame["close"]),
                       raw_price_warning="裸价格涨跌/回撤不是含分红投资回报；技术形态还须检查公司行为")
            row["raw_jump_dates_over_25pct"] = [str(d.date()) for d in frame.index[frame["close"].pct_change().abs() > 0.25]]
            if args.chart:
                try:
                    write_chart(frame, outdir / f"{code}_raw_kline.png", code)
                    row["chart_file"] = f"{code}_raw_kline.png"
                except (ValueError, ImportError) as exc:
                    row["chart_error"] = str(exc)
            if code in actions:
                book = ledger(frame, actions[code])
                book.to_csv(outdir / f"{code}_ledger.csv", index_label="date", mode="x")
                observed = book.loc[book["observed_close"], "wealth"]
                paths[code] = observed
                row.update(total_return=metrics(observed), action_source=actions[code]["source"],
                           action_notes=actions[code].get("notes"), ledger_file=f"{code}_ledger.csv")
            else:
                row["total_return_unavailable"] = "缺少有来源、覆盖足够区间且经审读的公司行为清单；未将空表当无股息/拆分"
        except (ValueError, KeyError, TypeError) as exc:
            row["analysis_error"] = str(exc)
        result["assets"][code] = clean(row)
    if len(paths) == len(bundle["assets"]) and len(paths) >= 2:
        try:
            weights = [float(w) for w in args.weights.split(",")] if args.weights else None
            result["comparison"], portfolio = compare_paths(paths, weights)
            if portfolio is not None:
                portfolio.to_csv(outdir / "portfolio_wealth.csv", index_label="date", header=["wealth_per_initial_unit"], mode="x")
        except ValueError as exc:
            result["comparison_error"] = str(exc)
    else:
        result["comparison_unavailable"] = "至少两只资产、各自完整可用总回报路径才比较；不静默丢掉失败资产或改权重"
    dump(outdir / "analysis.json", clean(result))
    write_report(result, outdir / "report.md")
    print(json.dumps({"report": str(outdir / "report.md"), "analysis": str(outdir / "analysis.json"),
                      "assets_with_total_return": len(paths)}, ensure_ascii=False))
    requested_portfolio_failed = args.weights and "portfolio" not in result.get("comparison", {})
    return 2 if requested_portfolio_failed or all("analysis_error" in row for row in result["assets"].values()) else 0


def write_report(result, path):
    def fmt(value):
        return "未知" if value is None else f"{value:.3f}"
    lines = ["# 市场研究计算结果", "", f"行情获取：{result.get('data_queried_at')}；请求截至：{result['requested_end']}",
             "", "本报告提供计算证据，投资判断还须结合产品持仓、估值、预算和投资目的。", "",
             "|标的|实际截至|收盘|MA20|MA60|含现金回报%|收盘最大回撤%|年化波动%|", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for code, row in result["assets"].items():
        technicals, risk = row.get("technical", {}), row.get("total_return", {})
        lines.append(f"|{code}|{row.get('data_end', '未知')}|{fmt(technicals.get('last_close'))}|{fmt(technicals.get('ma20'))}|{fmt(technicals.get('ma60'))}|{fmt(risk.get('cumulative_return_pct'))}|{fmt(risk.get('max_drawdown_pct'))}|{fmt(risk.get('annualized_volatility_pct'))}|")
    for code, row in result["assets"].items():
        if row.get("chart_file"):
            lines.extend(["", f"![{code}未复权K线]({row['chart_file']})"])
    lines.extend(["", "## 对比", ""])
    if "comparison" in result:
        for pair in result["comparison"]["pairs"]:
            lines.append(f"- {pair['left']}/{pair['right']}：日收益相关{fmt(pair['pearson_simple_returns'])}，{pair['observations']}个配对收益；条件为{pair['downside_condition']}时相关{fmt(pair['downside_correlation'])}，样本{pair['downside_observations']}。")
        comp = result["comparison"]
        if "portfolio" in comp:
            lines.extend([f"- 初始权重：{comp['weights']}；{comp['portfolio_assumptions']}", f"- 组合累计回报{fmt(comp['portfolio']['cumulative_return_pct'])}%，收盘最大回撤{fmt(comp['portfolio']['max_drawdown_pct'])}%。"])
    else:
        lines.append(result.get("comparison_error", result.get("comparison_unavailable", "无可比结果")))
    lines.extend(["", "## 数据限制", "", f"- {result['assumptions']}"])
    for code, row in result["assets"].items():
        if not row.get("matches_requested_end"):
            lines.append(f"- {code}历史末日与请求末日不相同；检查休市/更新延迟，不能冒充当日行情。")
        for key in ("total_return_unavailable", "analysis_error", "action_notes", "chart_error"):
            if row.get(key):
                lines.append(f"- {code}：{row[key]}")
        if "quote" in row:
            q = row["quote"]
            lines.append(f"- {code}报价时间{q['quote_time']}，报值溢价{fmt(q['last_vs_reported_iopv_pct'])}%，价差{fmt(q['spread_pct'])}%；{q['limitation']}。")
    for limitation in result["limitations"]:
        lines.append("- " + limitation)
    if result["fetch_failures"]:
        lines.append("- 取数失败详情见analysis.json中的fetch_failures。")
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    get = sub.add_parser("fetch", help="AKShare原价及指定ETF快照，输出JSON")
    get.add_argument("--codes", required=True, help="如sh515080,sh512890")
    get.add_argument("--kind", choices=["etf", "stock"], required=True)
    get.add_argument("--start", required=True)
    get.add_argument("--end", required=True)
    get.add_argument("--out", required=True)
    calc = sub.add_parser("analyze", help="离线技术/风险/对比；总回报需公司行为清单")
    calc.add_argument("--bundle", required=True)
    calc.add_argument("--actions", help="每个sh/sz代码对应reviewed/source/coverage_start/end/events的JSON")
    calc.add_argument("--weights", help="按bundle资产顺序的初始权重，如0.6,0.4；非再平衡策略")
    calc.add_argument("--chart", action="store_true", help="额外用matplotlib绘制近120交易日原价K线")
    calc.add_argument("--out", required=True, help="结果目录；请给每次研究独立目录")
    draft = sub.add_parser("prepare-actions", help="从ETF派息快照生成未审读公司行为草稿，不能直接用于总回报")
    draft.add_argument("--bundle", required=True)
    draft.add_argument("--out", required=True)
    held = sub.add_parser("holdings", help="同口径净值权重的持仓重叠与行业暴露；部分披露只报下界")
    held.add_argument("--profiles", required=True)
    held.add_argument("--out", required=True)
    args = parser.parse_args()
    try:
        if args.command == "fetch":
            dt.date.fromisoformat(args.start)
            dt.date.fromisoformat(args.end)
            if args.start >= args.end:
                raise ValueError("start须早于end")
            return fetch(args)
        if args.command == "prepare-actions":
            return prepare_actions(args)
        if args.command == "holdings":
            return holdings_command(args)
        return analyze(args)
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
