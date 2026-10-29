#!/usr/bin/env python3
"""ETF close/NAV history, peer and cross-border evidence. Offline verified inputs only."""
import argparse, datetime as dt, hashlib, json, math, statistics, sys
from pathlib import Path

def date(s): return dt.date.fromisoformat(s)
def val(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or x<=0: raise ValueError('价格和净值必须为正的有限数')
    return float(x)
def historical(data):
    cutoff=date(data['as_of']); assets=[]
    for asset in data['assets']:
        rows=[]; seen=set(); missing=[]
        for row in asset['rows']:
            d=date(row['date']); pub=date(row['nav_known_date'])
            if d in seen: raise ValueError('重复交易日')
            seen.add(d)
            if d>cutoff or pub>cutoff: missing.append({'date':str(d),'reason':'研究时点尚不可知'}); continue
            if pub<d: raise ValueError('净值可知日早于净值日')
            if not row.get('price_source') or not row.get('nav_source'): raise ValueError('需提供价格和净值来源')
            if row.get('close') is None or row.get('nav') is None:
                missing.append({'date':str(d),'reason':'价格或净值缺失'}); continue
            rows.append({'date':str(d),'nav_known_date':str(pub),'premium_pct':100*(val(row['close'])/val(row['nav'])-1)})
        rows.sort(key=lambda x:x['date']); values=[r['premium_pct'] for r in rows]
        # last value percentile uses midrank, reports sample size and exact comparison set
        rank=None if not values else 100*(sum(x<values[-1] for x in values)+0.5*sum(x==values[-1] for x in values))/len(values)
        run=0
        for row in reversed(rows):
            if row['premium_pct']<=0: break
            run+=1
        assets.append({'symbol':asset['symbol'],'peer_group':asset.get('peer_group'),'samples':len(rows),'series':rows,'latest_percentile_midrank':rank,'median_pct':statistics.median(values) if values else None,'consecutive_observed_premium_rows':run,'missing_or_unavailable':missing,'caveat':'按已提供且可知的观察行连续，不证明交易日历无缺口；正式净值事后公布，非盘中可得。'})
    pairs=[]
    for i,a in enumerate(assets):
        for b in assets[i+1:]:
            left={r['date']:r for r in a['series']}; right={r['date']:r for r in b['series']}
            common=sorted(set(left)&set(right))
            d=common[-1] if common else None
            pairs.append({'left':a['symbol'],'right':b['symbol'],'latest_common_date':d,'left_premium_pct':left[d]['premium_pct'] if d else None,'right_premium_pct':right[d]['premium_pct'] if d else None,'group_match':bool(a.get('peer_group') and a.get('peer_group')==b.get('peer_group')),'common_observations':len(common),'caveat':'同组标签只代表输入者分类；同日不保证同期盘中可交易，未返回标的不可补零。'})
    return {'as_of':data['as_of'],'assets':assets,'peer_comparisons':pairs,'note':'仅同日期收盘/净值，跨境估值时差仍存在；不同产品分组和来源须人工核验。'}

def peers(data):
    asof=dt.datetime.fromisoformat(data['as_of'])
    if asof.tzinfo is None: raise ValueError('as_of须带时区')
    max_age=val(data['max_age_seconds'])
    results=[]
    for row in data['assets']:
        out={'symbol':row['symbol'],'peer_group':row.get('peer_group'),'quote_time':row.get('quote_time'),'iopv_time':row.get('iopv_time'),'status':'unavailable','spread_pct':None,'ask_vs_iopv_pct':None,'reason':None}
        try:
            bid=val(row['bid']); ask=val(row['ask'])
            if bid>ask: raise ValueError('盘口买价高于卖价')
            out['spread_pct']=100*(ask-bid)/((ask+bid)/2)
            if not row.get('quote_source') or not row.get('quote_time'): raise ValueError('盘口来源或时间缺失')
            qt=dt.datetime.fromisoformat(row['quote_time'])
            if qt.tzinfo is None: raise ValueError('报价时间须带时区')
            qa=(asof-qt).total_seconds(); out['quote_age_seconds']=qa
            if qa<0 or qa>max_age: raise ValueError('盘口未来或过期')
            out['status']='book_observed'
            if row.get('iopv') is not None and row.get('iopv_time') and row.get('iopv_source'):
                qt=dt.datetime.fromisoformat(row['quote_time']); it=dt.datetime.fromisoformat(row['iopv_time'])
                if qt.tzinfo is None or it.tzinfo is None: raise ValueError('报价和IOPV时间须带时区')
                qa=(asof-qt).total_seconds(); ia=(asof-it).total_seconds()
                out['quote_age_seconds']=qa; out['iopv_age_seconds']=ia
                if qa<0 or ia<0 or qa>max_age or ia>max_age: raise ValueError('报价或IOPV未来、过期；拒算溢价')
                out['ask_vs_iopv_pct']=100*(ask/val(row['iopv'])-1)
                out['reason']='在用户设定的时效内的算术值；仍须核对底层市场、汇率和IOPV有效性，不自动视为可交易溢价'
            else: out['reason']='IOPV来源、时间或数值缺失，拒算实时溢价'
        except (ValueError,TypeError,KeyError) as e: out['reason']=str(e)
        results.append(out)
    return {'as_of':data.get('as_of'),'assets':results,'failed_or_partial':sum(1 for r in results if r['status']!='book_observed' or r['ask_vs_iopv_pct'] is None),'note':'各时间独立列示；未核验同步、历史回退、盘口容量和来源真实性，不能直接排序为买入优先级。'}

def crossborder(data):
    required=['fund_symbol','as_of','underlying_market_status','underlying_price_time','fx_time','iopv_time','creation_redemption_status','sources']
    missing=[k for k in required if not data.get(k)]
    evidence=data.get('sources',[])
    if not isinstance(evidence,list): raise ValueError('sources须为带时间和链接的列表')
    if any(not isinstance(e,dict) or not e.get('url') or not e.get('observed_at') for e in evidence): raise ValueError('每条证据须有url和observed_at')
    return {'fund_symbol':data.get('fund_symbol'),'evidence':data,'missing':missing,'sufficient_for_intraday_decision':False,'note':'只整理证据，不校验来源真实性或时效，不自动判断估值准确或交易可执行。核对海外休市、汇率、IOPV计算和申赎公告。'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('mode',choices=['history','peers','crossborder']); p.add_argument('--input',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    try:
        raw=Path(a.input).read_bytes(); data=json.loads(raw); out={'history':historical,'peers':peers,'crossborder':crossborder}[a.mode](data)
        out.update(input_path=str(Path(a.input).resolve()),input_sha256=hashlib.sha256(raw).hexdigest())
        with open(a.out,'x',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False)
        print('已保存',a.out)
    except (ValueError,KeyError,OSError,TypeError) as e: print(str(e),file=sys.stderr); return 2
    return 0
if __name__=='__main__': sys.exit(main())
