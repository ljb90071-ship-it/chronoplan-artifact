"""Sequential end-to-end logical epochs with response synthesis; no runtime benchmark."""
from collections import defaultdict
from pathlib import Path
import random,json
from check_response_synthesis import synthesize

def put(q,key,c,z):
    v=q[key];v[0]+=c;v[1]+=z

def oracle(rs,ss):
    q=defaultdict(lambda:[0,0])
    for k,g,a,b,x in rs:
        for sk,h,t,y in ss:
            if k==sk and a<=t<b:put(q,(k,g,h,t//3),1,x*y)
    return dict(q)

def main():
    total=replacements=0
    for seed in range(30):
        rng=random.Random(seed);fr=fs=0;rs=[];ss=[];pr=defaultdict(list);ps=[];q=defaultdict(lambda:[0,0])
        for epoch in range(60):
            dr=[(rng.randrange(2),rng.randrange(3),fr+rng.randrange(6),rng.randrange(1,7),rng.randrange(-4,5)) for _ in range(rng.randrange(1,4))]
            dr=[(k,g,a,a+d,x) for k,g,a,d,x in dr]
            ds=[(rng.randrange(2),rng.randrange(2),fs+rng.randrange(7),rng.randrange(-3,4)) for _ in range(rng.randrange(1,4))]
            for k,g,a,b,x in dr:
                for sk,h,t,y in ps:
                    if k==sk and a<=t<b:put(q,(k,g,h,t//3),1,x*y)
                pr[k,g].append((a,b,1,x))
            for k,h,t,y in ds:
                for (rk,g),rows in pr.items():
                    if rk==k:
                        for a,b,c,z in rows:
                            if a<=t<b:put(q,(k,g,h,t//3),c,z*y)
            rs+=dr;ss+=ds;ps+=ds
            fr+=rng.randrange(2);fs+=rng.randrange(2)
            ps=[s for s in ps if s[2]>=fr]
            before=dict((key,tuple(v)) for key,v in q.items())
            for kg,rows in list(pr.items()):
                if epoch%2==0:
                    pr[kg],_=synthesize(rows,fs);replacements+=1
                else:pr[kg]=[r for r in rows if r[1]>fs]
            assert before==dict((key,tuple(v)) for key,v in q.items())
            assert dict(q)==oracle(rs,ss),(seed,epoch)
            total+=1
    result=dict(seeds=30,logical_epochs=total,response_replacements=replacements,mismatches=0,scope='Sequential bilateral COUNT/SUM, independent frontiers, two join keys and both-side routing, repeated output-neutral synthesis. No concurrency, persistence, performance or PDF execution.')
    Path(__file__).with_name('synthesis-epoch-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
