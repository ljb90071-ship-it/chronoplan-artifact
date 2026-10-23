"""Per-target bounds and counterexamples to mixed-population median inference."""
import random
import sys
import unittest
from pathlib import Path
from statistics import median
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from chronoplan import CatchupTarget, response, reservation


class CapacityPopulation(unittest.TestCase):
    def test_medians_are_not_target_certificates(self):
        all_L=[1,1,1,100,100]
        completed=[(100,1,101),(100,1,101)]
        self.assertTrue(all(used<=L+U for L,U,used in completed))
        self.assertFalse(median(v[2] for v in completed)<=median(all_L)+median(v[1] for v in completed))
        all_L=[1,100,100]; completed=[(1,1,50)]
        self.assertFalse(all(used<=L+U for L,U,used in completed))
        self.assertTrue(median(v[2] for v in completed)<=median(all_L)+median(v[1] for v in completed))

    def test_individual_targets(self):
        rng=random.Random(1023)
        for _ in range(250):
            source=[]
            for _ in range(rng.randrange(1,30)):
                a=rng.randrange(20)
                source.append((a,a+rng.randrange(1,15),1,rng.randrange(-5,6)))
            frontier=rng.randrange(10); cap=rng.randrange(1,12)
            target=CatchupTarget(source,frontier,cap,10**9)
            for i in range(cap):
                a=rng.randrange(30); row=(a,a+rng.randrange(1,15),1,rng.randrange(-5,6))
                source.append(row)
                self.assertTrue(target.apply(row))
                if i%3==0:
                    frontier+=1;target.advance(frontier)
                self.assertLessEqual(len(target.rows),target.L+target.used)
                self.assertLessEqual(reservation(len(target.rows)),target.reserved_bytes)
                for t in range(frontier,46):
                    self.assertEqual(response(target.rows,t),response(source,t))
            # One further installation input must abort rather than cross the cap.
            self.assertFalse(target.apply((frontier,frontier+1,1,0)))
            with self.assertRaises(ValueError):target.install()

if __name__=='__main__':unittest.main()
