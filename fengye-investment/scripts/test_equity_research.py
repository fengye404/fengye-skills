"""Financial unit, publication-time and period-alignment regression checks."""
import json
from pathlib import Path
import unittest

from equity_research import calc


class EquityTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((Path(__file__).parents[1] / "examples/equity-input-example.json").read_text())

    def test_complete_synthetic_example(self):
        m = calc(self.data)["metrics"]
        self.assertEqual(m["pe_ttm"], 10)
        self.assertEqual(m["pb"], 2)
        self.assertAlmostEqual(m["historical_dividend_yield_tax_before"], 0.04)
        self.assertEqual(m["free_cash_flow"], 80000000)
        self.assertAlmostEqual(m["fcf_dividend_coverage"], 1.6)

    def test_loss_is_not_negative_pe_buy_signal(self):
        self.data["inputs"]["eps_ttm"]["value"] = -2
        self.assertIsNone(calc(self.data)["metrics"]["pe_ttm"])

    def test_future_publication_is_rejected(self):
        self.data["inputs"]["eps_ttm"]["disclosed_at"] = "2026-10-29"
        with self.assertRaises(ValueError):
            calc(self.data)

    def test_cash_flow_period_mismatch_blocks_fcf(self):
        self.data["inputs"]["capital_expenditure"]["period_start"] = "2026-01-01"
        m = calc(self.data)["metrics"]
        self.assertIsNone(m["free_cash_flow"])
        self.assertIsNone(m["fcf_dividend_coverage"])

    def test_payout_basis_mismatch_blocks_coverage(self):
        self.data["inputs"]["cash_dividends_paid"]["basis"] = "YTD"
        m = calc(self.data)["metrics"]
        self.assertEqual(m["free_cash_flow"], 80000000)
        self.assertIsNone(m["fcf_dividend_coverage"])

    def test_units_and_missing_values_are_not_silently_coerced(self):
        self.data["inputs"]["eps_ttm"]["value"] = None
        self.assertIsNone(calc(self.data)["metrics"]["pe_ttm"])
        self.data["inputs"]["price"]["unit"] = "万元"
        with self.assertRaises(ValueError):
            calc(self.data)

    def test_financial_company_does_not_get_industrial_fcf(self):
        self.data["industry"] = "银行"
        self.assertNotIn("fcf_dividend_coverage", calc(self.data)["metrics"])


if __name__ == "__main__":
    unittest.main()
