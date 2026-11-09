import unittest
import numpy as np
from organization import excursions

class ExcursionTests(unittest.TestCase):
    def score(self,states):
        s=np.array(states); return excursions(s==0,s==1,s!=2,2)
    def test_complete(self):
        e=self.score([0,0,1,1,1,0,0]); self.assertEqual(len(e),1); self.assertTrue(e[0]['complete'])
    def test_gap_splits(self):
        e=self.score([0,0,1,1,2,1,1,0,0]); self.assertEqual(len(e),2); self.assertFalse(any(x['complete'] for x in e))
    def test_short_touch_does_not_end(self):
        e=self.score([0,0,1,1,0,1,1,0,0]); self.assertEqual(len(e),1); self.assertEqual(e[0]['end'],7)
    def test_no_departure(self): self.assertEqual(self.score([0]*12),[])
    def test_end_censored(self): self.assertTrue(self.score([0,0,1,1])[0]['right_censored'])
    def test_initial_off_censored(self): self.assertTrue(self.score([1,1,0,0])[0]['left_censored'])

if __name__=='__main__': unittest.main()
