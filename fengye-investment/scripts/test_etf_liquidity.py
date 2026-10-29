import unittest

import pandas as pd

from etf_liquidity import analyze, date_index, observed_frame, quote_cost, window_stats


class LiquidityTests(unittest.TestCase):
    def frame(self):
        return observed_frame([{"date": "2026-01-05", "amount": 100},
                               {"date": "2026-01-06", "amount": 0},
                               {"date": "2026-01-07", "amount": 100}])

    def test_real_zero_is_retained_in_mean(self):
        result = window_stats(self.frame(), 3, order_amount=10)
        self.assertAlmostEqual(result["mean_amount_known_cny"], 200/3)
        self.assertEqual(result["reported_zero_amount_days"], 1)
        self.assertTrue(result["numeric_rows_complete"])
        self.assertFalse(result["complete_expected_sessions"])
        self.assertIsNotNone(result["calendar_coverage_warning"])
        self.assertFalse(result["hypothetical_order"]["denominator_is_complete_requested_window"])

    def test_missing_suspended_and_zero_are_distinct(self):
        frame = self.frame().iloc[:2]
        calendar = date_index(["2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"])
        result = window_stats(frame, 4, calendar, {"2026-01-07": "suspended"})
        self.assertEqual(result["declared_suspended_days"], 1)
        self.assertEqual(result["reported_zero_amount_days"], 1)
        self.assertEqual(result["missing_or_unknown_days"], 1)
        self.assertEqual(result["known_amount_days"], 3)
        self.assertAlmostEqual(result["mean_amount_known_cny"], 100/3)
        self.assertEqual(result["mean_amount_active_known_cny"], 50)
        self.assertFalse(result["numeric_rows_complete"])

    def test_zero_low_turnover_is_not_infinite_liquidity(self):
        result = window_stats(self.frame(), 3, order_amount=10)
        self.assertGreater(result["hypothetical_order"]["pct_of_p10_known_turnover"], result["hypothetical_order"]["pct_of_mean_known_turnover"])
        zero = observed_frame([{"date": "2026-01-05", "amount": 0}])
        self.assertIsNone(window_stats(zero, 1, order_amount=10)["hypothetical_order"]["pct_of_mean_known_turnover"])

    def test_round_trip_has_two_half_spreads_not_two_full_spreads(self):
        quote = {"买一": 0.999, "卖一": 1.001, "更新时间": "2026-01-05T15:00:00+08:00"}
        one = quote_cost(quote, 10000, 0.0001)
        both = quote_cost(quote, 10000, 0.0001, side="roundtrip")
        self.assertAlmostEqual(one["midpoint_spread_reference_cny"], 10)
        self.assertAlmostEqual(one["commission_plus_spread_reference_cny"], 11)
        self.assertAlmostEqual(both["midpoint_spread_reference_cny"], 20)
        self.assertAlmostEqual(both["commission_plus_spread_reference_cny"], 22)

    def test_missing_book_and_unspecified_commission_stay_unknown(self):
        result = quote_cost(None, 10000, 0.0001, min_commission=5)
        self.assertEqual(result["commission_reference_cny"], 5)
        self.assertIn("spread_unavailable", result)
        self.assertNotIn("commission_plus_spread_reference_cny", result)
        self.assertIsNone(quote_cost({}, 10000)["commission_reference_cny"])

    def test_invalid_amount_dates_and_suspension_conflict_rejected(self):
        with self.assertRaises(ValueError):
            observed_frame([{"date": "2026-01-05", "amount": -1}])
        with self.assertRaises(ValueError):
            date_index(["2026-01-05", "2026-01-05"])
        with self.assertRaises(ValueError):
            window_stats(self.frame(), 3, statuses={"2026-01-05": "suspended"})

    def test_false_source_placeholder_is_unknown_not_zero_turnover(self):
        frame = observed_frame([{"date": "2026-01-05", "amount": False}, {"date": "2026-01-06", "amount": 100}])
        result = window_stats(frame, 2)
        self.assertEqual(result["missing_or_unknown_days"], 1)
        self.assertEqual(result["reported_zero_amount_days"], 0)

    def test_failed_asset_retained_and_future_values_excluded(self):
        bundle = {"requested_end": "2026-01-06", "assets": {
            "a": {"history_status": "ok", "history": [{"date": "2026-01-05", "amount": 100}, {"date": "2026-01-06", "amount": 100}, {"date": "2026-01-07", "amount": 1000000}]},
            "b": {"history_status": "unavailable"}}}
        result = analyze(bundle, [2], "CNY", 10)
        self.assertEqual(result["assets"]["a"]["window_stats"][0]["mean_amount_known_cny"], 100)
        self.assertIn("error", result["assets"]["b"])
        with self.assertRaises(ValueError):
            analyze(bundle, [2], "USD")


if __name__ == "__main__":
    unittest.main()
