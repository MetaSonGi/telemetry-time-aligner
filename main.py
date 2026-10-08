"""비동기 PLC·로봇 센서 데이터를 같은 시점의 트윈 스냅샷으로 정렬하고 오래된 값과 미래값 누출을 구분합니다."""
import argparse, json, math, html
from pathlib import Path

def finite(value, name, minimum=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(name + ': finite number required')
    if minimum is not None and value < minimum:
        raise ValueError(name + ': below minimum')
    return value

def report(result, title):
    payload=html.escape(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    return '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:32px auto;padding:20px;background:#101b2b;color:#ecf4ff}pre{padding:24px;background:#192b40;border-radius:12px;white-space:pre-wrap;overflow-wrap:anywhere}h1{color:#80e4c5}</style><h1>'+html.escape(title)+'</h1><p>오프라인 샘플 계산 결과 · 실물 장비 연결 없음</p><pre>'+payload+'</pre></html>'

def cli(run,title):
    parser=argparse.ArgumentParser(description=title)
    parser.add_argument('--input',default=str(Path(__file__).with_name('sample-input.json')))
    parser.add_argument('--html',help='optional standalone HTML result path')
    args=parser.parse_args()
    try:
        data=json.loads(Path(args.input).read_text(encoding='utf-8'))
        result=run(data)
        if args.html: Path(args.html).write_text(report(result,title),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))
    except (ValueError,KeyError,TypeError) as exc:
        parser.exit(2, 'input error: '+str(exc)+'\n')

from bisect import bisect_right

def run(data):
    tolerance=finite(data['tolerance_s'],'tolerance_s',0)
    streams={}; duplicates=0
    for r in data['readings']:
        asset=r['asset_id']; sensor=r['sensor_id']
        if not isinstance(asset,str) or not asset or not isinstance(sensor,str) or not sensor:
            raise ValueError('nonempty asset/sensor IDs required')
        t=finite(r['time_s'],'time_s',0);finite(r['value'],'value')
        version=r['sequence']
        if type(version) is not int or version<0: raise ValueError('nonnegative sequence required')
        key=(asset,sensor);bucket=streams.setdefault(key,{})
        if t in bucket:
            duplicates+=1
            if version==bucket[t]['sequence'] and r['value']!=bucket[t]['value']:
                raise ValueError('conflicting equal-sequence reading')
            if version<=bucket[t]['sequence']:continue
        bucket[t]=dict(r)
    ordered={key:sorted(bucket.items()) for key,bucket in streams.items()}
    snapshots=[]
    for target in data['snapshot_times_s']:
        target=finite(target,'snapshot_time',0); values=[]
        for (asset,sensor),items in sorted(ordered.items()):
            ix=bisect_right([x[0] for x in items],target)-1
            base={'asset_id':asset,'sensor_id':sensor}
            if ix<0:values.append({**base,'status':'missing','value':None});continue
            source_t,r=items[ix];age=target-source_t;fresh=age<=tolerance
            values.append({**base,'status':'fresh' if fresh else 'stale','value':r['value'] if fresh else None,
                           'source_time_s':source_t,'age_s':round(age,6),'sequence':r['sequence']})
        snapshots.append({'time_s':target,'values':values})
    return {'policy':'backward_asof_no_future','duplicate_timestamps':duplicates,'snapshots':snapshots}

if __name__ == "__main__": cli(run,'센서 시간 정렬기')
