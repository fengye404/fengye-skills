#!/usr/bin/env python3
"""A-share raw snapshots and transparent, manually verified financial calculations."""
import argparse, datetime as dt, hashlib, json, math, multiprocessing as mp, os, re, sys
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Asia/Shanghai')
def now(): return dt.datetime.now(TZ).isoformat(timespec='seconds')
def worker(name, code, queue):
    try:
        import akshare as ak
        import pandas as pd
        calls = {
          'finance': lambda: ak.stock_financial_abstract_ths(symbol=code, indicator='按报告期'),
          'dividends': lambda: ak.stock_fhps_detail_em(symbol=code),
          'valuation': lambda: ak.stock_value_em(symbol=code),
          'price': lambda: ak.stock_zh_a_hist(symbol=code, period='daily', adjust='', timeout=15),
        }
        frame = calls[name]()
        # pandas JSON converts NaN/NaT to null; no source values are inferred.
        rows = json.loads(frame.to_json(orient='records', date_format='iso', force_ascii=False))
        queue.put({'status':'ok', 'rows':rows, 'columns':list(frame.columns), 'count':len(rows), 'akshare_version':ak.__version__})
    except Exception as e: queue.put({'status':'error','error':f'{type(e).__name__}: {e}'})

def snapshot(code, timeout):
    if not re.fullmatch(r'\d{6}',code): raise ValueError('A股代码须为六位数字')
    sources={}
    urls={'finance':'https://basic.10jqka.com.cn/new/'+code+'/finance.html','dividends':'https://data.eastmoney.com/yjfp/detail/'+code+'.html','valuation':'https://data.eastmoney.com/gzfx/detail/'+code+'.html','price':'https://quote.eastmoney.com/'}
    for name in urls:
        q=mp.Queue(); p=mp.Process(target=worker,args=(name,code,q)); p.start()
        try: result=q.get(timeout=timeout)
        except Exception:
            result={'status':'timeout','error':f'超过 {timeout} 秒或子进程无结果'}
        if p.is_alive(): p.terminate()
        p.join()
        sources[name]={'source_url':urls[name], 'endpoint':{'finance':'stock_financial_abstract_ths','dividends':'stock_fhps_detail_em','valuation':'stock_value_em','price':'stock_zh_a_hist'}[name], 'queried_at':now(), **result}
        q.close()
    return {'schema':'equity-raw-v1','symbol':code,'market':'中国内地A股','queried_at':now(),'price_adjust':'未复权','sources':sources,'note':'原始接口行不保证公告时点或最新；未核验财务单位/公司行为，不可直接作交易建议。'}

def calc(data):
    required=['symbol','as_of','market','industry','sources','inputs']
    for k in required:
        if k not in data: raise ValueError('缺少 '+k)
    dt.date.fromisoformat(data['as_of'])
    i=data['inputs']; warnings=[]; metrics={}
    def number(key):
        item=i.get(key)
        if item is None: warnings.append(key+' 缺失'); return None
        if not isinstance(item,dict) or not item.get('source') or not item.get('date') or not item.get('unit'):
            raise ValueError(key+' 必须包括 value、source、date、unit')
        dt.date.fromisoformat(item['date'])
        if item['date'] > data['as_of']: raise ValueError(key+' 日期晚于分析时点')
        if key in ('eps_ttm','book_value_per_share','operating_cash_flow','capital_expenditure','cash_dividends_paid'):
            disclosed=item.get('disclosed_at')
            if not disclosed: raise ValueError(key+' 缺少公开日期 disclosed_at')
            dt.date.fromisoformat(disclosed)
            if disclosed > data['as_of']: raise ValueError(key+' 公开日期晚于分析时点')
        val=item.get('value')
        if val is None: warnings.append(key+' 缺失'); return None
        if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(val): raise ValueError(key+' 必须是有限数值')
        return val
    def ratio(label, numerator, denominator):
        if numerator is not None and denominator is not None and denominator>0: metrics[label]=numerator/denominator
        else: metrics[label]=None
    price=number('price'); eps=number('eps_ttm'); bvps=number('book_value_per_share'); div=number('dividend_per_share_ttm')
    if price is not None and price <= 0: raise ValueError('price 必须大于0')
    for k in ['price','eps_ttm','book_value_per_share','dividend_per_share_ttm']:
        if i.get(k) and i[k].get('value') is not None and i[k]['unit']!='元/股': raise ValueError(k+' 单位须为元/股')
    ratio('pe_ttm',price,eps); ratio('pb',price,bvps); ratio('historical_dividend_yield_tax_before',div,price)
    if eps is not None and eps<=0: warnings.append('TTM盈利非正，PE不适用；不判为低估')
    if bvps is not None and bvps<=0: warnings.append('每股净资产非正，PB不适用')
    if div is not None and div<0: raise ValueError('股息不得为负')
    if div is not None and not data.get('dividend_window_verified'): warnings.append('现金股息窗口、已实施状态或拆分影响尚未核验，股息率仅为输入算术值')
    if data['industry'] in ('银行','保险'): warnings.append('金融机构不机械采用工业企业自由现金流覆盖率')
    else:
        ocf=number('operating_cash_flow'); capex=number('capital_expenditure'); payout=number('cash_dividends_paid')
        for k in ['operating_cash_flow','capital_expenditure','cash_dividends_paid']:
            if i.get(k) and i[k].get('value') is not None and i[k]['unit']!='元': raise ValueError(k+' 单位须为元')
        if capex is not None and capex<0: raise ValueError('资本支出使用正的现金流出金额')
        if payout is not None and payout<0: raise ValueError('现金股利使用正的流出金额')
        def period(key):
            item=i.get(key)
            if item is None or item.get('value') is None: return None
            if not all(item.get(k) for k in ('period_start','period_end','basis')):
                raise ValueError(key+' 必须提供 period_start、period_end、basis')
            start=dt.date.fromisoformat(item['period_start']); end=dt.date.fromisoformat(item['period_end'])
            if start>end or end>dt.date.fromisoformat(data['as_of']): raise ValueError(key+' 财务期间无效')
            return (start,end,item['basis'])
        periods=[period(k) for k in ('operating_cash_flow','capital_expenditure','cash_dividends_paid')]
        fcf=ocf-capex if ocf is not None and capex is not None and periods[0]==periods[1] else None
        if ocf is not None and capex is not None and periods[0]!=periods[1]: warnings.append('经营现金流与资本支出期间或口径不一致；拒算自由现金流')
        if payout is not None and fcf is not None and periods[0]!=periods[2]: warnings.append('股息与自由现金流期间或口径不一致；拒算覆盖率')
        metrics['free_cash_flow']=fcf; ratio('fcf_dividend_coverage',fcf,payout if periods[0]==periods[2] else None)
        warnings.append('自由现金流覆盖率仅适合同期同口径现金流；需排查一次性因素')
    return {'schema':'equity-analysis-v1','symbol':data['symbol'],'as_of':data['as_of'],'market':data['market'],'industry':data['industry'],'inputs':i,'sources':data['sources'],'metrics':metrics,'warnings':warnings,'scope':'算术结果不是估值结论或买卖建议；财务发布日期、期间、股本、税及派息事件须独立核实。'}

def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='cmd',required=True)
    s=sub.add_parser('snapshot'); s.add_argument('--symbol',required=True); s.add_argument('--timeout',type=int,default=20); s.add_argument('--output',required=True)
    a=sub.add_parser('analyze'); a.add_argument('--input',required=True); a.add_argument('--output',required=True)
    x=p.parse_args()
    try:
        if x.cmd=='snapshot': result=snapshot(x.symbol,x.timeout)
        else:
            raw=Path(x.input).read_bytes()
            result=calc(json.loads(raw)); result['input_path']=str(Path(x.input).resolve()); result['input_sha256']=hashlib.sha256(raw).hexdigest()
        # Exclusive creation prevents overwriting an earlier research snapshot.
        with open(x.output,'x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
        print('已保存',x.output)
        if x.cmd=='snapshot' and any(v['status']!='ok' for v in result['sources'].values()): print('部分接口失败；详见JSON',file=sys.stderr)
    except Exception as e: print(f'{type(e).__name__}: {e}',file=sys.stderr); return 1
    return 0
if __name__=='__main__': mp.freeze_support(); sys.exit(main())
