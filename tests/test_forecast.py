import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from planner import *

class ForecastTests(unittest.TestCase):
    def test_actions(self):
        self.assertIn(('MergeRetain','Projected'),actions(['Endpoint','Endpoint'],'Retain'))
        self.assertNotIn(('Replace','Projected'),actions(['Endpoint','Endpoint'],'Retain'))
        self.assertIn(('Replace','Projected'),actions(['Endpoint','Endpoint'],'ChronoPlan'))
        self.assertFalse(any('Retain' in a[0] for a in actions(['Endpoint','Endpoint'],'EagerSynth')))
    def test_build(self):
        x=construction(.8,.2,100,.0002,1000,4096)
        self.assertAlmostEqual(x['drain_s'],4/9)
        self.assertEqual((x['catchup_records'],x['installation_records']),(445,1))
        self.assertAlmostEqual(x['one_time_cpu'],.889)
        self.assertFalse(construction(.8,.2,100,.002,1000,4096)['feasible'])
        self.assertFalse(construction(.8,.2,100,.0002,1000,445)['feasible'])
    def test_population(self):
        self.assertEqual(lifetime_bins([1,2,3,4],1),[(1,1),(1,2),(2,4)])
        p=Population([(10,10)],[(1,5)],2)
        self.assertEqual(p.at(2),14);self.assertEqual(p.at(10),10)
        self.assertEqual(p.removals(9,11),14)
        self.assertEqual(coefficient({1:10,3:30},3),10)
    def test_units(self):
        p=Population([(100,inf)],[],0)
        x=integrate(p,{'probes':2,'matches':3},{'lookup':{0:.01},'payload':{0:.001}},96,8192,horizon=90)
        self.assertAlmostEqual(x['cpu_core_s'],90*.026)
        self.assertAlmostEqual(x['memory_gib_s'],90*17792/2**30)
        self.assertAlmostEqual(x['tail_cpu_core_s'],30*.026)
        x=integrate(p,{}, {},96,8192,install_s=10,source_bytes=100,target_reservation=200,scratch_buffer_bytes=50)
        self.assertAlmostEqual(x['memory_gib_s'],(10*350+50*17792)/2**30)

    def test_source_target_phases(self):
        old=Population([(100,inf)],[]);new=Population([(20,inf)],[])
        a=integrate(old,{'probes':2},{'lookup':{0:.1}},96,8192,install_s=10,
                    source_bytes=1000,target_reservation=2000,start_s=0,end_s=10)
        b=integrate(new,{'probes':2},{'lookup':{0:.01}},96,8192,install_s=10,
                    start_s=10,end_s=60,population_origin_s=10)
        self.assertAlmostEqual(a['cpu_core_s']+b['cpu_core_s'],10*.2+50*.02)
        self.assertAlmostEqual(a['memory_gib_s']+b['memory_gib_s'],(10*3000+50*(1920+8192))/2**30)

if __name__=='__main__':unittest.main()
