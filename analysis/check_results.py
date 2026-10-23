"""Check arithmetic of paper summary data and recompute exact shape counts."""
from pathlib import Path
import csv,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from chronoplan import synthesize,reservation
def read(name):
    with (ROOT/'results'/name).open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
mixed={r['policy']:r for r in read('mixed.csv')}
cp=mixed['ChronoPlan']; reductions={}
for baseline in ['Retain','EagerSynth']:
    reductions[baseline]={k:round(100*(1-float(cp[k])/float(mixed[baseline][k])),1) for k in ['integrated_gib_min','p99_ms']}
assert reductions=={'Retain':{'integrated_gib_min':4.5,'p99_ms':2.7},'EagerSynth':{'integrated_gib_min':1.7,'p99_ms':7.6}}
assert float(mixed['EagerSynth']['sealed_core_s'])==0
for r in read('shapes.csv'):
    n=int(r['n']); name=r['shape']
    rows={'adjacent':[(i,i+1,1,1) for i in range(n)],'disjoint':[(2*i,2*i+1,1,1) for i in range(n)],'staggered':[(i,100+i,1,1) for i in range(n)]}[name]
    target,m=synthesize(rows,0)
    assert (m,len(target),96*len(target))==(int(r['m']),int(r['L']),int(r['entry_bytes']))
decisions=read('decisions.csv')
for r in decisions:
    assert sum(int(r[k]) for k in ['replace','preserve','stay'])==int(r['candidates'])
    assert round(reservation(int(r['L'])+4096)/2**20,3)==float(r['reserved_mib'])
    # Different populations: do not infer a per-target bound from these medians.
shares={k:sum(int(r[k]) for r in decisions)/400 for k in ['replace','preserve','stay']}
assert shares=={'replace':.46,'preserve':.31,'stay':.23}
for r in read('saturation.csv'):
    assert abs(float(r['rate_million_records_s'])*1200/1000-float(r['measured_billion_records']))<1e-9
print(json.dumps({'status':'passed','relative_reductions_percent':reductions,'decision_shares':shares,'matched_records':600000*1200},indent=2))

from statistics import median
trials=read('mixed_trials.csv')
for policy in ['Retain','EagerSynth','ChronoPlan']:
    selected=[r for r in trials if r['policy']==policy]
    for metric in ['peak_gib','integrated_gib_min','converted_gib','sealed_core_s','p99_ms','planner_percent']:
        assert median(float(r[metric]) for r in selected)==float(mixed[policy][metric])
paired={}
for metric in ['integrated_gib_min','p99_ms']:
    cp={r['trial']:float(r[metric]) for r in trials if r['policy']=='ChronoPlan'}
    eager={r['trial']:float(r[metric]) for r in trials if r['policy']=='EagerSynth'}
    diffs=[eager[k]-cp[k] for k in sorted(cp)]
    paired[metric]={'differences':diffs,'min':min(diffs),'max':max(diffs)}
assert (paired['integrated_gib_min']['min'],paired['integrated_gib_min']['max'])==(2,3)
assert (paired['p99_ms']['min'],paired['p99_ms']['max'])==(8,10)
for cap,expected in [(1024,11),(4096,4),(8192,2)]:
    rows=[r for r in read('attempts.csv') if int(r['update_cap'])==cap]
    assert all(int(r['commits'])+int(r['allowance_aborts'])==int(r['attempts']) for r in rows)
    assert median(100*int(r['allowance_aborts'])/int(r['attempts']) for r in rows)==expected
print(json.dumps({'paired_ranges':paired,'capacity_validation':'per-target tests; no mixed-median inference'},indent=2))
