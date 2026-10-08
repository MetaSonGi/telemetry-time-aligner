import unittest,json
from pathlib import Path
from main import *
class Tests(unittest.TestCase):
    def sample(self):return json.loads(Path(__file__).with_name('sample-input.json').read_text(encoding='utf-8'))

    def test_no_future_and_boundary(self):
        d=self.sample(); d['snapshot_times_s']=[0,3,4]
        out=run(d)['snapshots'];self.assertTrue(all(v['status']=='missing' for v in out[0]['values']))
        self.assertEqual(out[1]['values'][1]['status'],'fresh')
        self.assertEqual(out[2]['values'][1]['value'],34.5)
    def test_stale_not_zero(self):
        d=self.sample();d['snapshot_times_s']=[8]
        values=run(d)['snapshots'][0]['values'];self.assertIsNone(values[1]['value']);self.assertEqual(values[1]['status'],'stale')
    def test_order_independent_and_duplicate(self):
        d=self.sample();a=run(d);d['readings'].reverse();self.assertEqual(a,run(d));self.assertEqual(a['duplicate_timestamps'],1)
    def test_bad_input(self):
        d=self.sample();d['tolerance_s']=-1
        with self.assertRaises(ValueError):run(d)
        d=self.sample();r=dict(d['readings'][0]);r['value']=99;d['readings'].append(r)
        with self.assertRaises(ValueError):run(d)

if __name__=="__main__":unittest.main()
