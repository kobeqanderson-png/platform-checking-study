import unittest
import numpy as np
from tracking_qc import short_fill, smooth, derivative, platform_events, unwrap_segments


class GapTests(unittest.TestCase):
    def test_long_gap_not_partially_filled(self):
        x=np.array([0.,np.nan,np.nan,np.nan,np.nan,5.])
        y,_=short_fill(x,3)
        self.assertTrue(np.isnan(y[1:5]).all())
        z,_=short_fill(x,4)
        np.testing.assert_allclose(z,np.arange(6))

    def test_edges_never_filled(self):
        y,_=short_fill(np.array([np.nan,1.,np.nan,3.,np.nan]),2)
        self.assertTrue(np.isnan(y[[0,4]]).all())
        self.assertEqual(y[2],2)

    def test_no_derivative_or_smoothing_across_gap(self):
        x=np.array([0.,0.,np.nan,100.,100.])
        y=smooth(x,3)
        self.assertTrue(np.isnan(y[2]))
        self.assertTrue(np.isnan(derivative(y,30)[3]))
        np.testing.assert_allclose(y[[0,1,3,4]],[0,0,100,100])

    def test_unknown_does_not_count_as_off_or_repeat_departure(self):
        b=np.array([[0,0],[0,0],[2,0],[2,0],[np.nan,np.nan],[2,0],[2,0]],float)
        on,off,e=platform_events(b,np.array([0,0]),1,2)
        self.assertFalse(on[4] or off[4])
        self.assertEqual(len(e),1)
        self.assertTrue(e[0]['exact'])

    def test_gap_before_departure_gives_interval(self):
        b=np.array([[0,0],[np.nan,np.nan],[2,0],[2,0]],float)
        _,_,e=platform_events(b,np.array([0,0]),1,2)
        self.assertFalse(e[0]['exact'])
        self.assertEqual((e[0]['lower_s'],e[0]['upper_s']),(.5,1.))

    def test_angle_recovers_after_gap(self):
        t=unwrap_segments(np.array([3.,-3.,np.nan,1.,1.1]))
        self.assertTrue(np.isfinite(t[-1]))
        self.assertLess(abs(t[1]-t[0]),1)


if __name__=='__main__': unittest.main()
