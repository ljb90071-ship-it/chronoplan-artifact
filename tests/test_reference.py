import random, sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from chronoplan import *


class ReferenceTests(unittest.TestCase):
    def test_catchup_gap_and_abort(self):
        old = [(0,2,1,1),(4,6,1,1)]
        target = CatchupTarget(old,0,1,100000)
        self.assertTrue(target.apply((1,8,1,2)))
        self.assertEqual(len(target.install()),3)
        self.assertEqual(len(synthesize(old+[(1,8,1,2)],0)[0]),5)
        for t in range(10):
            self.assertEqual(response(target.rows,t),response(old+[(1,8,1,2)],t))
        self.assertFalse(target.apply((2,9,1,0)))
        with self.assertRaises(ValueError): target.install()
        self.assertEqual(old,[(0,2,1,1),(4,6,1,1)])

    def test_boundary_and_zero_sum(self):
        rows,m = synthesize([(0,6,1,2),(0,6,1,-2)],2)
        self.assertEqual(rows,[(2,6,2,0)])
        self.assertEqual(response(rows,6),(0,0))
        self.assertEqual(m,1)
        self.assertEqual(synthesize([(i,i+1,1,1) for i in range(20)],0)[0],[(0,20,1,1)])

    def test_capacity_and_installation_batch(self):
        old=[(0,6,1,2)]
        denied=CatchupTarget(old,0,2,reservation(3)-1)
        self.assertFalse(denied.active)
        with self.assertRaises(ValueError): denied.install()
        t=CatchupTarget(old,0,2,reservation(3))
        self.assertTrue(t.apply((1,7,1,-2)))
        t.advance(6)
        self.assertTrue(t.apply((6,9,1,3))) # Installation epoch consumes allowance.
        for probe in range(6,11):
            self.assertEqual(response(t.install(),probe),response(old+[(1,7,1,-2),(6,9,1,3)],probe))
        with self.assertRaises(ValueError): t.advance(5)
        self.assertFalse(t.apply((7,10,1,4)))

    def test_planner(self):
        stay=Action('stay',0,100,0)
        self.assertEqual(choose(stay,[Action('replace',10,40,0),Action('preserve',1,70,0)]),'replace')
        self.assertEqual(choose(stay,[Action('replace',10,40,0,feasible=False)]),'stay')
        self.assertEqual(choose(stay,[Action('replace',10,40,0)],cooldown_elapsed=False),'stay')
        self.assertEqual(choose(stay,[Action('replace',10,89,0)]),'stay')

    def test_engine_against_history(self):
        for seed in range(20):
            rng=random.Random(seed); e=EpochEngine(); rs=[]; ss=[]
            for epoch in range(40):
                dr=[]
                for _ in range(rng.randrange(1,4)):
                    a=e.fr+rng.randrange(6)
                    dr.append((rng.randrange(2),rng.randrange(3),a,a+rng.randrange(1,7),rng.randrange(-4,5)))
                ds=[(rng.randrange(2),rng.randrange(2),e.fs+rng.randrange(7),rng.randrange(-3,4)) for _ in range(rng.randrange(1,4))]
                q=e.epoch(dr,ds,e.fr+rng.randrange(2),e.fs+rng.randrange(2),replace=epoch%2==0)
                rs+=dr;ss+=ds; truth=defaultdict(lambda:[0,0])
                for k,g,a,b,x in rs:
                    for sk,h,t,y in ss:
                        if k==sk and a<=t<b:
                            v=truth[k,g,h,t//3];v[0]+=1;v[1]+=x*y
                self.assertEqual(q,{k:tuple(v) for k,v in truth.items()})

    def test_admission_atomic(self):
        e=EpochEngine();e.epoch([],[],2,2)
        with self.assertRaises(ValueError): e.epoch([(0,0,2,3,1)],[(0,0,1,1)],2,2)
        self.assertFalse(e.intervals)
        with self.assertRaises(ValueError): e.epoch([],[],1,2)

if __name__=='__main__': unittest.main()
