"""Gap-aware tracking QC. Thresholds are analysis choices, not biological limits."""
import numpy as np
import pandas as pd
from scipy import signal

SPOTS = {'kac_d8': (870., 50.), 'kac_d6': (310., 210.)}


def runs(mask, minimum=1):
    edges = np.diff(np.r_[False, np.asarray(mask, bool), False].astype(int))
    return [(int(a), int(b)) for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)) if b-a >= minimum]


def finite(x):
    return np.isfinite(x) if x.ndim == 1 else np.isfinite(x).all(axis=1)


def short_fill(x, max_frames, max_step=None):
    """Fill an ENTIRE internal gap only if <= max_frames. Never edge-fill.

    Unlike pandas limit_direction='both', a long gap is not partially filled.
    max_step bounds the implied displacement per frame for vector coordinates.
    """
    y = np.array(x, dtype=float, copy=True)
    good = finite(y)
    filled = np.zeros(len(y), bool)
    for a, b in runs(~good):
        if a == 0 or b == len(y) or b-a > max_frames:
            continue
        if max_step is not None and np.linalg.norm(y[b]-y[a-1])/(b-a+1) > max_step:
            continue
        y[a:b] = np.linspace(y[a-1], y[b], b-a+2)[1:-1]
        filled[a:b] = True
    return y, filled


def smooth(x, n, method='median'):
    """Smooth independently inside finite runs, retaining all long-gap NaNs."""
    y = np.full_like(x, np.nan, dtype=float)
    for a, b in runs(finite(x)):
        obj = pd.Series(x[a:b]) if x.ndim == 1 else pd.DataFrame(x[a:b])
        roller = obj.rolling(max(1, int(n)), center=True, min_periods=1)
        y[a:b] = getattr(roller, method)().to_numpy()
    return y


def unwrap_segments(theta):
    out = np.full_like(theta, np.nan)
    for a, b in runs(np.isfinite(theta)):
        out[a:b] = np.unwrap(theta[a:b])
    return out


def derivative(x, fps):
    # NaN at the first sample of every segment: no derivative crosses a gap.
    return np.concatenate([np.full_like(x[:1], np.nan), np.diff(x, axis=0)], axis=0) * fps


def angle_signal(a, b, fps, valid=None):
    delta = a-b
    theta = np.arctan2(delta[:,1], delta[:,0])
    theta[np.linalg.norm(delta, axis=1) < 1] = np.nan
    if valid is not None:
        theta[~valid] = np.nan
    return unwrap_segments(theta)


def clean_track(df, pool, cond, fps, speed_limit=60., spot_radius=40., rim_limit=.98):
    parts = list(df.columns.get_level_values(0).unique())
    raw = {p: df[p][['x','y']].to_numpy(float).copy() for p in parts}
    lk = {p: df[p]['likelihood'].to_numpy(float).copy() for p in parts}
    body = raw['spine_mid'].copy()
    fallback = (~np.isfinite(lk['spine_mid'])) | (lk['spine_mid'] < .3)
    body[fallback] = raw['head_center'][fallback]
    unsure = fallback & ((lk['head_center'] < .3) | ~np.isfinite(lk['head_center']))
    body[unsure] = np.nan
    radius = np.linalg.norm(body-np.array(pool[:2]), axis=1)
    outside = radius > rim_limit*pool[2]
    spot = np.linalg.norm(body-np.array(SPOTS[cond]), axis=1) <= spot_radius if cond in SPOTS else np.zeros(len(body), bool)
    common = ~finite(body) | outside | spot
    candidate = body.copy()
    candidate[common] = np.nan
    candidate = smooth(candidate, max(3, int(fps*.2)) | 1)
    speed = np.linalg.norm(derivative(candidate, fps), axis=1)*86/pool[2]
    jumps = np.flatnonzero(speed > speed_limit)
    speed_bad = np.zeros(len(body), bool)
    speed_bad[jumps] = True
    speed_bad[np.maximum(jumps-1, 0)] = True
    common |= speed_bad
    candidate[common] = np.nan
    candidate, interpolated = short_fill(candidate, round(.5*fps), speed_limit*pool[2]/86/fps)
    clean = {'body': candidate, 'body_raw': body, 'valid': finite(candidate), 'body_interpolated': interpolated,
             'rejected': common, 'spot_rejected': spot, 'outside_rejected': outside, 'speed_rejected': speed_bad}
    for p in parts:
        xy = raw[p].copy()
        bad = common | (lk[p] < .3) | ~np.isfinite(lk[p])
        xy[bad] = np.nan
        xy, filled = short_fill(xy, round(.5*fps))
        xy = smooth(xy, max(3,int(fps*.2)) | 1)
        # A body gap invalidates the whole pose, even if one keypoint has shorter gaps.
        xy[~clean['valid']] = np.nan
        clean[p] = xy
        clean[p+'_lk'] = lk[p]
        clean[p+'_interpolated'] = filled
    return clean


def platform_events(body, platform, radius, fps):
    """Unknown time is neither on nor off, and cannot generate a new departure.

    A long-gap onset gives an interval-censored departure. Off segments interrupted
    by unknown time remain one episode unless a new observed on-platform frame occurs.
    """
    valid = finite(body)
    inside = valid & (np.linalg.norm(body-platform, axis=1) <= radius)
    outside = valid & ~inside
    events = []
    last_on_used = -2
    for a,b in runs(outside, fps):
        prev_on = np.flatnonzero(inside[:a])
        last_on = int(prev_on[-1]) if len(prev_on) else -1
        if last_on == last_on_used:
            continue
        last_on_used = last_on
        exact = (a == 0) or (last_on == a-1)
        events.append(dict(frame=a, end=b, exact=exact, lower_s=(last_on+1)/fps, upper_s=a/fps))
    return inside, outside, events


def swings(theta, eligible, fps, amplitude_deg, order_seconds=.15):
    events = []
    for a,b in runs(np.isfinite(theta) & eligible, 3):
        v=theta[a:b]
        hi=signal.find_peaks(v, distance=max(1,round(fps*order_seconds)))[0]
        lo=signal.find_peaks(-v, distance=max(1,round(fps*order_seconds)))[0]
        ex=sorted(set(hi.tolist()+lo.tolist()))
        for i,j in zip(ex[:-1],ex[1:]):
            d=np.degrees(v[j]-v[i])
            if abs(d)>=amplitude_deg:
                events.append((a+i,a+j,d))
    return events


def peaks_in_segments(x, eligible, fps, prominence, height=None, spacing=.5):
    found=[]
    for a,b in runs(np.isfinite(x) & eligible, 3):
        found.extend((signal.find_peaks(x[a:b],prominence=prominence,height=height,
                                      distance=max(1,round(spacing*fps)))[0]+a).tolist())
    return found
