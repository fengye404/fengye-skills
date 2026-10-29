#!/usr/bin/env python3
"""Compare unchanged holdings and fixed hypothetical ETF trades; no orders are sent."""
import argparse, datetime as dt, hashlib, json, math, sys
from pathlib import Path
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

def finite(v):
    if isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v): raise ValueError('非有限数值')
    return float(v)
def whole(v):
    if isinstance(v,bool) or not isinstance(v,int) or v<0: raise ValueError('持有份额及交易份额须为非负整数')
    return v

def simulate(data, use_trades):
    dates=data['dates']; prices=data['prices']; config=data['costs']; positions={k:whole(v) for k,v in data['initial_shares'].items()}
    symbols=list(positions); cash=finite(data['initial_cash']); events=data['corporate_actions']; trades=data['trades'] if use_trades else []
    if cash<0 or not symbols or not dates: raise ValueError('缺初始持仓、现金或日期')
    parsed=[dt.date.fromisoformat(d) for d in dates]
    if parsed!=sorted(set(parsed)): raise ValueError('日期必须唯一且递增')
    if not data.get('price_source') or not data.get('price_adjustment')=='raw': raise ValueError('必须提供未复权价格来源')
    if not events.get('reviewed') or not events.get('source') or events['coverage_start']>dates[0] or events['coverage_end']<dates[-1]: raise ValueError('公司行为需来源、审读及完整覆盖')
    commission=finite(config['commission_rate']); minimum=finite(config['minimum_commission']); slip=finite(config['slippage_rate']); lot=whole(config['buy_lot']); tick=finite(config['price_tick'])
    if commission<0 or minimum<0 or slip<0 or slip>=1 or lot<=0 or tick<=0: raise ValueError('成本参数无效')
    if any(t['date'] not in dates or t['symbol'] not in symbols or t['side'] not in ['buy','sell'] for t in trades): raise ValueError('交易日期、标的或方向无效')
    actions=events.get('events',[]); claims={}; receivables={}; ledger=[]; fills=[]; event_keys=set()
    for idx,e in enumerate(actions):
        if e['symbol'] not in positions: raise ValueError('公司行为标的不在持仓列表')
        if e['type']=='dividend':
            key=('dividend',e['symbol'],e['record_date'],e['ex_date'],e['pay_date'])
            if key in event_keys: raise ValueError('重复分红事件，须先核验')
            event_keys.add(key)
            record,ex,pay=[dt.date.fromisoformat(e[k]) for k in ('record_date','ex_date','pay_date')]
            if not record<ex<=pay or finite(e['cash_per_unit'])<0: raise ValueError('分红日期或金额无效')
            if record < parsed[0] <= pay: raise ValueError('期初存在历史登记的未派股息，当前模型未实现期初应收，拒算')
            if dates[0] <= str(record) <= dates[-1] and (str(record) not in dates or (str(ex)<=dates[-1] and str(ex) not in dates) or (str(pay)<=dates[-1] and str(pay) not in dates)): raise ValueError('登记、除息或派发日缺估值日历；不得静默漏记现金')
        elif e['type']=='split':
            key=('split',e['symbol'],e['effective_date'])
            if key in event_keys: raise ValueError('重复拆分事件，须先核验')
            event_keys.add(key)
            if finite(e['ratio'])<=0 or e['effective_date'] not in dates: raise ValueError('拆分日缺价格或比例无效')
        else: raise ValueError('不支持的公司行为')
    for d in dates:
        if set(prices.get(d,{}))!=set(symbols): raise ValueError('每个日期需全部标的的有效收盘价')
        close={s:finite(prices[d][s]) for s in symbols}
        if any(p<=0 for p in close.values()): raise ValueError('价格必须为正')
        for idx,e in enumerate(actions):
            if e['type']=='split' and e['effective_date']==d:
                q=positions[e['symbol']]*e['ratio']
                if not float(q).is_integer(): raise ValueError('拆分产生碎份，须显式处理')
                positions[e['symbol']]=int(q)
            if e['type']=='dividend' and e['ex_date']==d and idx in claims: receivables[idx]=claims[idx]
            if e['type']=='dividend' and e['pay_date']==d and idx in receivables: cash+=receivables.pop(idx)
        sellable=dict(positions)
        for t in [t for t in trades if t['date']==d]:
            s=t['symbol']; q=whole(t['shares']); side=t['side']
            if q==0 or (side=='buy' and q%lot): raise ValueError('数量必须大于零；买入须整手')
            theoretical=Decimal(str(close[s]))*(Decimal('1')+(Decimal(str(slip)) if side=='buy' else -Decimal(str(slip))))
            tick_d=Decimal(str(tick)); rounded=(theoretical/tick_d).to_integral_value(rounding=ROUND_CEILING if side=='buy' else ROUND_FLOOR)*tick_d
            px=float(rounded)
            if px<=0: raise ValueError('按最小价位取整后成交价无效')
            gross=px*q; fee=max(minimum,gross*commission)
            if side=='buy':
                if cash+1e-9<gross+fee: raise ValueError('现金不足，未建模融资')
                positions[s]+=q; cash-=gross+fee
            else:
                if sellable[s]<q: raise ValueError('卖出超过日初可卖份额；默认T+1保守约束')
                positions[s]-=q; sellable[s]-=q; cash+=gross-fee
                if cash < -1e-9: raise ValueError('卖出后现金不足以支付佣金')
            fills.append({'date':d,'symbol':s,'side':side,'shares':q,'reference_close':close[s],'assumed_execution_price':px,'fee':fee})
        for idx,e in enumerate(actions):
            if e['type']=='dividend' and e['record_date']==d: claims[idx]=positions[e['symbol']]*e['cash_per_unit']
        wealth=cash+sum(positions[s]*close[s] for s in symbols)+sum(receivables.values())
        if wealth<=0: raise ValueError('财富必须为正')
        ledger.append({'date':d,'positions':positions.copy(),'cash':cash,'receivable':sum(receivables.values()),'wealth':wealth})
    peak=ledger[0]['wealth']; maxdd=0
    for row in ledger: peak=max(peak,row['wealth']); maxdd=min(maxdd,row['wealth']/peak-1)
    return {'ledger':ledger,'fills':fills,'final_wealth':ledger[-1]['wealth'],'return_pct':100*(ledger[-1]['wealth']/ledger[0]['wealth']-1),'max_drawdown_pct':100*maxdd}

def run(data):
    # Establish starting value before any transaction; day-0 switch incurs costs.
    if any(t['date']==data['dates'][0] for t in data['trades']): raise ValueError('初始日不得交易；从下一交易日开始比较，确保成本计入收益')
    baseline=simulate(data,False); strategy=simulate(data,True)
    return {'baseline':baseline,'switch':strategy,'difference_final_wealth':strategy['final_wealth']-baseline['final_wealth'],'assumptions':'同日起始持仓和现金；明确订单按当日收盘价加减滑点模拟，事前固定，不能用当日收盘信号同价成交；现金零息，税及其他费用未模拟；不模拟盘口深度、涨跌停、停牌、部分成交；交易不自动执行。真实市场规则按产品核验。'}

def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True); p.add_argument('--out',required=True); a=p.parse_args()
    try:
        raw=Path(a.input).read_bytes(); data=json.loads(raw); result=run(data); result.update(input_path=str(Path(a.input).resolve()),input_sha256=hashlib.sha256(raw).hexdigest())
        with open(a.out,'x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False)
        print('已保存',a.out)
    except (ValueError,KeyError,TypeError,OSError) as e: print(str(e),file=sys.stderr); return 2
    return 0
if __name__=='__main__': sys.exit(main())
