"""Run either example from any working directory."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from chronoplan import endpoint, synthesize, EpochEngine

path = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'examples/synthesis.json'
data = json.loads(path.read_text(encoding="utf-8"))
if 'rows' in data:
    base, changes = endpoint(data['rows'], data['frontier'])
    rows, m = synthesize(data['rows'], data['frontier'])
    print(json.dumps(dict(base=base, derivatives=changes, target=rows, m=m, L=len(rows)), indent=2))
else:
    engine = EpochEngine(data['window'], data['duration'])
    for number, batch in enumerate(data['epochs'], 1):
        q = engine.epoch(**batch)
        print(json.dumps(dict(epoch=number, output=[dict(key=k,count=v[0],sum=v[1]) for k,v in sorted(q.items())]), indent=2))
