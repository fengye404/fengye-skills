import copy, json, unittest
from pathlib import Path
import etf_premium as premium
import etf_switch as switch
BASE=Path(__file__).resolve().parent.parent
class PremiumTest(unittest.TestCase):
 def setUp(self): self.data=json.loads((BASE/'examples/etf-premium-example.json').read_text())
 def test_percent(self):
  r=premium.historical(self.data); self.assertAlmostEqual(r['assets'][0]['series'][0]['premium_pct'],1); self.assertAlmostEqual(r['assets'][1]['series'][0]['premium_pct'],2)
 def test_not_published(self):
  self.data['as_of']='2026-01-06'; r=premium.historical(self.data); self.assertEqual(r['assets'][0]['samples'],1); self.assertEqual(r['assets'][1]['samples'],0)
 def test_missing_and_duplicate(self):
  self.data['assets'][0]['rows'][0]['nav']=None; self.assertEqual(len(premium.historical(self.data)['assets'][0]['missing_or_unavailable']),1)
  self.data['assets'][0]['rows'].append(copy.deepcopy(self.data['assets'][0]['rows'][0])); self.assertRaises(ValueError,premium.historical,self.data)
 def test_peers_missing_iopv_time(self):
  data={'as_of':'2026-01-09T15:00:00+08:00','max_age_seconds':120,'assets':[{'symbol':'A','bid':1,'ask':1.01,'quote_time':'2026-01-09T14:59:00+08:00','quote_source':'example','iopv':1,'iopv_source':'example'}]}
  r=premium.peers(data); self.assertEqual(r['failed_or_partial'],1); self.assertIsNone(r['assets'][0]['ask_vs_iopv_pct']); self.assertIsNotNone(r['assets'][0]['spread_pct'])
 def test_peers_stale_rejected(self):
  data={'as_of':'2026-01-09T15:00:00+08:00','max_age_seconds':60,'assets':[{'symbol':'A','bid':1,'ask':1.01,'quote_time':'2026-01-09T14:58:00+08:00','quote_source':'example','iopv':1,'iopv_time':'2026-01-09T14:59:30+08:00','iopv_source':'example'}]}
  r=premium.peers(data); self.assertIsNone(r['assets'][0]['ask_vs_iopv_pct']); self.assertIn('过期',r['assets'][0]['reason']); self.assertEqual(r['assets'][0]['status'],'unavailable')
 def test_crossborder_never_greenlights(self):
  r=premium.crossborder({'fund_symbol':'x','sources':[]}); self.assertFalse(r['sufficient_for_intraday_decision']); self.assertTrue(r['missing'])
class SwitchTest(unittest.TestCase):
 def setUp(self): self.data=json.loads((BASE/'examples/etf-switch-example.json').read_text())
 def test_dividend_and_trade(self):
  r=switch.run(self.data); self.assertAlmostEqual(r['switch']['ledger'][2]['receivable'],10); self.assertAlmostEqual(r['baseline']['ledger'][2]['receivable'],20); self.assertAlmostEqual(r['switch']['ledger'][-1]['receivable'],0); self.assertAlmostEqual(sum(x['fee'] for x in r['switch']['fills']),.2)
 def test_duplicate_events_rejected(self):
  self.data['corporate_actions']['events'].append(copy.deepcopy(self.data['corporate_actions']['events'][0])); self.assertRaises(ValueError,switch.run,self.data)
 def test_tick_rounding(self):
  self.data['costs']['slippage_rate']=0.00012; self.data['costs']['price_tick']=0.01
  r=switch.run(self.data); self.assertAlmostEqual(r['switch']['fills'][0]['assumed_execution_price'],9.99); self.assertAlmostEqual(r['switch']['fills'][1]['assumed_execution_price'],10.01)
 def test_zero_after_tick_rejected(self):
  self.data['prices']['2026-01-06']['A']=0.001; self.data['costs']['price_tick']=0.01
  self.assertRaisesRegex(ValueError,'成交价无效',switch.run,self.data)
 def test_missing_price(self):
  del self.data['prices']['2026-01-07']['A']; self.assertRaises(ValueError,switch.run,self.data)
 def test_oversell(self):
  self.data['trades'][0]['shares']=300; self.assertRaises(ValueError,switch.run,self.data)
 def test_initial_trade(self):
  self.data['trades'][0]['date']='2026-01-05'; self.assertRaises(ValueError,switch.run,self.data)
 def test_prior_entitlement(self):
  e=self.data['corporate_actions']['events'][0]; e.update(record_date='2026-01-02',ex_date='2026-01-05'); self.assertRaises(ValueError,switch.run,self.data)
 def test_same_day_buy_then_sell(self):
  self.data['trades']=[{'date':'2026-01-06','symbol':'B','side':'buy','shares':100},{'date':'2026-01-06','symbol':'B','side':'sell','shares':100}]; self.assertRaises(ValueError,switch.run,self.data)
if __name__=='__main__': unittest.main()
