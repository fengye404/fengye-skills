"""Offline economic-invariant tests; run with the investment Python environment."""
import unittest
import tempfile
from pathlib import Path

import pandas as pd

from market_research import compare_holdings, compare_paths, dump, history_frame, ledger, metrics, quote_diagnostics


def prices(rows):
    return history_frame([{"date": d, "close": p} for d, p in rows])


def actions(events, start="2026-01-01", end="2026-01-31"):
    return {"reviewed": True, "source": "synthetic economic test", "coverage_start": start,
            "coverage_end": end, "events": events}


class EconomicTests(unittest.TestCase):
    def test_snapshots_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "snapshot.json"
            dump(path, {"version": 1})
            with self.assertRaises(FileExistsError):
                dump(path, {"version": 2})
            self.assertIn('"version": 1', path.read_text())

    def test_duplicate_events_are_rejected(self):
        frame = prices([("2026-01-05", 10), ("2026-01-06", 5)])
        event = {"type": "split", "effective_date": "2026-01-06", "ratio": 2}
        with self.assertRaises(ValueError):
            ledger(frame, actions([event, event]))

    def test_partial_holdings_are_not_normalized_to_full_portfolio(self):
        a = {"source": "synthetic", "as_of": "2026-06-30", "scope": "top10", "holdings": [{"code": "x", "weight": 0.1, "sector": "bank"}]}
        b = {"source": "synthetic", "as_of": "2026-06-30", "scope": "full", "holdings": [{"code": "x", "weight": 0.2, "sector": "bank"}, {"code": "y", "weight": 0.8}]}
        result = compare_holdings({"a": a, "b": b})
        self.assertAlmostEqual(result["pairs"][0]["weighted_overlap_of_nav"], 0.1)
        self.assertAlmostEqual(result["assets"]["a"]["coverage_of_nav"], 0.1)

    def test_dividend_ex_and_payment_do_not_create_wealth(self):
        frame = prices([("2026-01-05", 10), ("2026-01-06", 9.9), ("2026-01-07", 9.9)])
        book = ledger(frame, actions([{"type": "dividend", "record_date": "2026-01-05",
            "ex_date": "2026-01-06", "pay_date": "2026-01-07", "cash_per_unit": 0.1}]))
        self.assertAlmostEqual(book.loc["2026-01-06", "receivable"], 0.1)
        self.assertAlmostEqual(book.loc["2026-01-07", "cash"], 0.1)
        self.assertAlmostEqual(book["wealth"].min(), 10)
        self.assertAlmostEqual(book["wealth"].max(), 10)

    def test_buying_on_ex_date_has_no_entitlement(self):
        frame = prices([("2026-01-06", 9.9), ("2026-01-07", 9.9)])
        book = ledger(frame, actions([{"type": "dividend", "record_date": "2026-01-05",
            "ex_date": "2026-01-06", "pay_date": "2026-01-07", "cash_per_unit": 0.1}]))
        self.assertEqual(book["cash"].sum(), 0)
        self.assertEqual(book["receivable"].sum(), 0)

    def test_nontrading_split_keeps_value_and_changes_units(self):
        frame = prices([("2026-01-09", 10), ("2026-01-12", 5)])
        book = ledger(frame, actions([{"type": "split", "effective_date": "2026-01-10", "ratio": 2}]))
        self.assertEqual(book.loc["2026-01-10", "shares"], 2)
        self.assertEqual(book["wealth"].tolist(), [10, 10, 10])

    def test_dividend_entitlement_not_doubled_by_later_split(self):
        frame = prices([("2026-01-05", 10), ("2026-01-06", 4.95), ("2026-01-07", 4.95)])
        book = ledger(frame, actions([
            {"type": "dividend", "record_date": "2026-01-05", "ex_date": "2026-01-06", "pay_date": "2026-01-07", "cash_per_unit": 0.1},
            {"type": "split", "effective_date": "2026-01-06", "ratio": 2}]))
        self.assertAlmostEqual(book.iloc[-1]["cash"], 0.1)
        self.assertAlmostEqual(book.iloc[-1]["wealth"], 10)

    def test_unknown_actions_and_missing_ex_price_are_rejected(self):
        frame = prices([("2026-01-05", 10), ("2026-01-07", 9.9)])
        with self.assertRaises(ValueError):
            ledger(frame, {"reviewed": False})
        with self.assertRaises(ValueError):
            ledger(frame, actions([{"type": "dividend", "record_date": "2026-01-05", "ex_date": "2026-01-06", "pay_date": "2026-01-07", "cash_per_unit": 0.1}]))

    def test_metrics_include_peak_and_recovery(self):
        wealth = prices([("2026-01-05", 100), ("2026-01-06", 80), ("2026-01-07", 110)])["close"]
        m = metrics(wealth)
        self.assertAlmostEqual(m["max_drawdown_pct"], -20)
        self.assertAlmostEqual(m["cumulative_return_pct"], 10)
        self.assertEqual(m["recovery_date"], "2026-01-07")

    def test_comparison_does_not_hide_unmatched_days_or_bad_weights(self):
        a = prices([("2026-01-05", 10), ("2026-01-06", 11), ("2026-01-07", 10)])["close"]
        with self.assertRaises(ValueError):
            compare_paths({"a": a, "b": a.iloc[1:]})
        with self.assertRaises(ValueError):
            compare_paths({"a": a, "b": a}, [0.6, 0.6])
        _, p = compare_paths({"a": a, "b": a}, [0.6, 0.4])
        self.assertAlmostEqual(p.iloc[-1], 1)

    def test_stale_quote_and_unknown_iopv_time_are_not_live_clearance(self):
        q = quote_diagnostics({"最新价": 1.2, "买一": 1.199, "卖一": 1.2,
                               "IOPV实时估值": 1.2, "更新时间": "2026-01-05T15:00:00+08:00"}, "2026-01-06")
        self.assertFalse(q["quote_matches_requested_date"])
        self.assertFalse(q["executable_premium_verified"])
        self.assertIsNone(q["iopv_time"])


if __name__ == "__main__":
    unittest.main()
