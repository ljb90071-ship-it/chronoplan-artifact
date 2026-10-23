"""Evaluate the paper's illustrative capacity/cost example, not a system trace."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from chronoplan import Action,choose,reservation
from planner import actions,construction,Population,integrate
out={}
for shape,L in [('disjoint',20000),('staggered',39999)]:
    bounds={'Stay':0,'Replace':reservation(L+4096),'MergeRetain':2*2**20}
    ledger={'Stay':Action('Stay',0,3,100,.2),
            'Replace':Action('Replace',.8,1.8,30,.1,bounds['Replace']<=3*2**20),
            'MergeRetain':Action('MergeRetain',.2,2.2,60,.1,True)}
    choices={}
    for policy in ['Retain','EagerSynth','ChronoPlan']:
        allowed={kind for kind,layout in actions(['Endpoint','Endpoint'],policy)
                 if layout=='Projected' or kind=='Stay'}
        choices[policy]=choose(ledger['Stay'],[a for k,a in ledger.items() if k!='Stay' and k in allowed])
    out[shape]={'L':L,'reserved_bytes':bounds,'choices':choices}
assert out['disjoint']['choices']=={'Retain':'MergeRetain','EagerSynth':'Replace','ChronoPlan':'Replace'}
assert out['staggered']['choices']=={'Retain':'MergeRetain','EagerSynth':'Stay','ChronoPlan':'MergeRetain'}
out['construction_example']=construction(.8,.2,100,.0002,1000,4096)
out['constant_population_example']=integrate(Population([(100,float('inf'))],[]),
    {'probes':2,'matches':3},{'lookup':{0:.01},'payload':{0:.001}},96,8192,horizon=90)
print(json.dumps(out,indent=2))
