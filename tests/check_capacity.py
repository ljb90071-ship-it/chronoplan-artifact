from pathlib import Path
import ctypes, json
from check_response_synthesis import synthesize
class Node(ctypes.Structure):
    _fields_=[('ends',ctypes.c_int64*2),('payload',ctypes.c_uint64*4),('links',ctypes.c_uint64*3),('max_end',ctypes.c_int64),('flags_alignment',ctypes.c_ubyte*16)]
assert ctypes.sizeof(Node)==96
report={}
for name,rows in [('disjoint',[(2*i,2*i+1,1,1) for i in range(20000)]),('staggered',[(i,20000+i,1,1) for i in range(20000)])]:
    target,m=synthesize(rows,0);L=len(target);N=L+4096;bound=96*N+8192
    actual_reservation=4096+((96*N+4095)//4096)*4096
    assert actual_reservation<=bound
    report[name]=dict(n=len(rows),m=m,L=L,latest_end=max(x[1] for x in rows),reserved_bytes=bound,reserved_MiB=bound/2**20,target_allowance_MiB=3,fits=bound<=3*2**20)
assert [report[x]['L'] for x in report]==[20000,39999]
assert all(x['m']==39999 and x['latest_end']==39999 for x in report.values())
assert [round((96*(L+4096)+8192)/2**20,3) for L in [8192,15564]]==[1.133,1.808]
assert [sum(x)/400 for x in [(120,64),(48,76),(32,60)]]==[.46,.31,.23]
report['node_size']=ctypes.sizeof(Node)
report['scope']='Actual response scans, illustrative ctypes layout and arithmetic under the specified allocator; no streaming implementation or measured memory/performance.'
Path(__file__).with_name('capacity-check.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
