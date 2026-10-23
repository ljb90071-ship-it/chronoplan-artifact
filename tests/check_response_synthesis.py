"""Exact response synthesis checks; no streaming/performance implementation."""
from pathlib import Path
from collections import defaultdict
from itertools import combinations_with_replacement
import random,json

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from chronoplan import synthesize, response


def main():
    domain=[(a,b,1,z) for a in range(4) for b in range(a+1,6) for z in (-2,0,3)]
    bags=[()]+[(x,) for x in domain]+list(combinations_with_replacement(domain,2))
    cases=probes=0
    for rows in bags:
        for f in range(7):
            target,m=synthesize(rows,f)
            assert len(target)<=m
            assert all(target[i][1]<=target[i+1][0] for i in range(len(target)-1))
            assert synthesize(target,f)[0]==target
            for t in range(f,8):
                assert response(rows,t)==response(target,t)
                probes+=1
            cases+=1
    # Repeated synthesis, new input, two old generation unions, and independently advancing frontiers.
    epochs=queries=0
    for seed in range(120):
        rng=random.Random(seed); originals=[];physical=[];f=0
        for epoch in range(80):
            for j in range(rng.randrange(1,5)):
                a=rng.randrange(max(0,f-4),f+9);b=a+rng.randrange(1,7);z=rng.randrange(-5,6)
                originals.append((a,b,1,z));physical.append((a,b,1,z))
            if epoch%3==0: physical,_=synthesize(physical,f)
            f+=rng.randrange(0,3)
            physical=[r for r in physical if r[1]>f]
            for t in range(f,f+16):
                assert response(originals,t)==response(physical,t)
                queries+=1
            epochs+=1
    long_chain=[(i,i+1,1,2) for i in range(20)]
    chain,_=synthesize(long_chain,0)
    assert chain==[(0,20,1,2)] # internal support may exceed ingress D=1
    # A cost-sensitive counterexample, not CPU performance.
    old=[(0,10,1,2),(1,10,1,-1)]
    rebuilt,_=synthesize(old,5)
    assert rebuilt==[(5,10,2,1)]
    n=20
    distinct=[(i,100+i,1,i+1) for i in range(n)]
    target,_=synthesize(distinct,0)
    assert len(target)==2*n-1
    expansion_runs=len(target)
    gap_old=[(0,2,1,1),(4,6,1,1)]
    gap_new=[(1,8,1,2)]
    gap_target,m=synthesize(gap_old,0)
    canonical,_=synthesize(gap_old+gap_new,0)
    appended=gap_target+gap_new
    assert len(canonical)==5 and len(appended)==3
    assert len(canonical)>len(gap_target)+2
    assert all(response(canonical,t)==response(appended,t) for t in range(10))
    catchup_cases=0
    for rows in bags:
        for f in range(3):
            target,m=synthesize(rows,f)
            for new in domain:
                live=[new] if new[1]>f else []
                appended=target+live
                regroup={}
                for a,b,c,z in appended:
                    prev=regroup.get((a,b),(0,0));regroup[(a,b)]=(prev[0]+c,prev[1]+z)
                assert len(regroup)<=len(target)+1
                canon,_=synthesize(list(rows)+[new],f)
                assert len(canon)<=m+2
                for probe in range(f,7):assert response(appended,probe)==response(list(rows)+[new],probe)
                catchup_cases+=1
    shape_counts={}
    for name,rows in [('adjacent',[(i,i+1,1,1) for i in range(20)]),('disjoint',[(2*i,2*i+1,1,1) for i in range(20)]),('staggered',[(i,100+i,1,1) for i in range(20)])]:
        target_shape,m_shape=synthesize(rows,0);shape_counts[name]=dict(m=m_shape,L=len(target_shape),bytes=96*len(target_shape))
    assert [(v['m'],v['L']) for v in shape_counts.values()]==[(1,1),(39,20),(39,39)]
    report=dict(shape_counts=shape_counts,exhaustive_states=cases,response_probes=probes,random_epochs=epochs,random_probes=queries,
                catchup_cases=catchup_cases,gap_example=dict(snapshot_runs=2,canonical_after_one_update=5,append_target_entries=3),shared_end_synthetic_rows=rebuilt,long_chain_internal_D_counterexample=chain,
                expansion_example=dict(original_projected_entries=n,synthetic_runs=expansion_runs),
                scope='Exact integer response algebra and count of entries only; no performance, WAL, concurrency or PDF verification.')
    p=Path(__file__).with_name('response-synthesis-results.json');p.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
