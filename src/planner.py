"""Bounded forecast arithmetic; inputs are profiles, not measured by this module."""
from dataclasses import dataclass
from math import ceil, log2, inf
LAYOUTS = ('Projected', 'Split', 'Endpoint')

def actions(layouts, policy):
    if not 1 <= len(layouts) <= 2 or any(x not in LAYOUTS for x in layouts):
        raise ValueError('One or two known layouts required')
    if policy not in ('ChronoPlan','EagerSynth','Retain'):
        raise ValueError('Unknown policy')
    out=[('Stay',layouts[-1])]
    for y in LAYOUTS:
        forward=all(x==y or x=='Projected' or y=='Endpoint' for x in layouts)
        if (policy!='Retain' or forward) and not (len(layouts)==1 and layouts[0]==y):
            out.append(('Replace',y))
    if policy!='EagerSynth':
        for y in LAYOUTS:
            if len(layouts)==2 or y!=layouts[0]:
                out.append(('Retain' if len(layouts)==1 else 'MergeRetain',y))
    return out

def coefficient(table, population):
    if not table: raise ValueError('Missing primitive calibration')
    b=min(31,ceil(log2(max(0,population)+1)))
    return table[min(table,key=lambda j:(abs(j-b),j))]

def lifetime_bins(distances, velocity):
    if velocity<0 or any(d<0 for d in distances):raise ValueError('Negative progress')
    groups={}
    for d in distances:
        j=min(31,max(0,ceil(log2(max(1,d)))))
        groups.setdefault(j,[]).append(d)
    return [(len(ds),inf if velocity==0 else (2**j if j<31 else max(ds))/velocity)
            for j,ds in sorted(groups.items())]

@dataclass
class Population:
    initial: list  # (count, lifetime seconds)
    future: list   # (probability, lifetime seconds)
    births_per_second: float=0
    def at(self,t):
        return sum(n for n,l in self.initial if t<l)+self.births_per_second*sum(p*min(t,l) for p,l in self.future)
    def removals(self,left,right):
        return sum(n for n,l in self.initial if left<=l<right)+self.births_per_second*sum(p*(max(0,right-l)-max(0,left-l)) for p,l in self.future if l!=inf)

def construction(initial_cpu,builder_cores,interval_rate,catchup_cpu,total_rate,cap):
    if min(initial_cpu,interval_rate,catchup_cpu,total_rate,cap)<0 or builder_cores<=0:
        raise ValueError('Invalid construction inputs')
    tb=initial_cpu/builder_cores
    mu=inf if catchup_cpu==0 else builder_cores/catchup_cpu
    if mu<=interval_rate:return {'feasible':False,'reason':'catchup_service'}
    tc=0 if mu==inf else interval_rate*tb/(mu-interval_rate)
    count=ceil(interval_rate*(tb+tc))
    batch=ceil(interval_rate*min(.005,4096/total_rate)) if total_rate else 0
    return dict(feasible=count+batch<=cap,build_s=tb,drain_s=tc,install_s=tb+tc,
                catchup_records=count,installation_records=batch,
                one_time_cpu=initial_cpu+count*catchup_cpu)

def cells(horizon,install):
    for lo,hi in ((0,60),(60,horizon)):
        if hi<=lo:continue
        edges=[lo+(hi-lo)*i/64 for i in range(65)]
        if lo<install<hi:edges.append(install)
        edges=sorted(set(edges))
        yield from zip(edges,edges[1:])

def integrate(population,rates,calibration,bytes_per_key,header_bytes,horizon=60,
              install_s=0,source_bytes=0,target_reservation=0,scratch_buffer_bytes=0,
              retain_reservation=False,start_s=0,end_s=None,population_origin_s=0):
    """Integrate one phase/population profile; sum profiles for complete actions.

    Primitive rates are inserts/s, probes/s, matches/probe and transfers/s.
    Coefficients are core-s/operation by size bucket. Before installation,
    source/target/scratch allocations are supplied explicitly; the caller must
    use disjoint start_s/end_s phases and population_origin_s for state age. No migration
    CPU is included here. Occupied target bytes are not added to its reservation.
    """
    if horizon<60:raise ValueError('Comparison horizon must be at least 60 seconds')
    end_s=horizon if end_s is None else end_s
    if not 0<=population_origin_s<=start_s<=end_s<=horizon:
        raise ValueError("Invalid phase bounds or population origin")
    cpu=mem=tailcpu=tailmem=0.0
    for left,right in cells(horizon,install_s):
        left=max(left,start_s);right=min(right,end_s)
        if right<=left:continue
        t=(left+right)/2;dt=right-left;n=population.at(t-population_origin_s)
        counts={'insert':rates.get('inserts',0)*dt,'lookup':rates.get('probes',0)*dt,
                'payload':rates.get('probes',0)*min(n,rates.get('matches',0))*dt,
                'transfer':rates.get('transfers',0)*dt,'remove':population.removals(left-population_origin_s,right-population_origin_s)}
        c=sum(v*coefficient(calibration[k],n) for k,v in counts.items() if v)
        occupied=bytes_per_key*ceil(n)+header_bytes
        held=(source_bytes+target_reservation+scratch_buffer_bytes if t<install_s
              else max(occupied,target_reservation) if retain_reservation else occupied)
        m=held*dt/2**30
        cpu+=c;mem+=m
        if left>=60:tailcpu+=c;tailmem+=m
    return dict(cpu_core_s=cpu,memory_gib_s=mem,tail_cpu_core_s=tailcpu,tail_memory_gib_s=tailmem)
