import math
from pathlib import Path


def rk4_simulate(omega0, gamma, x0, v0, dt, steps):
    """RK4 simulation of damped harmonic oscillator."""
    def f(x, v):
        return v, -gamma * v - omega0**2 * x
    
    results = [(0.0, x0, v0)]
    x, v = x0, v0
    t = 0.0
    for i in range(steps):
        k1x, k1v = f(x, v)
        k2x, k2v = f(x + dt/2*k1x, v + dt/2*k1v)
        k3x, k3v = f(x + dt/2*k2x, v + dt/2*k2v)
        k4x, k4v = f(x + dt*k3x, v + dt*k3v)
        x = x + dt/6*(k1x + 2*k2x + 2*k3x + k4x)
        v = v + dt/6*(k1v + 2*k2v + 2*k3v + k4v)
        t += dt
        results.append((t, x, v))
    return results


def compute_expected():
    data = rk4_simulate(2.0, 0.5, 1.0, 0.0, 0.01, 2000)
    velocities = [d[2] for d in data]
    
    v_min = min(velocities)
    v_max = max(velocities)
    n_bins = 20
    w = (v_max - v_min) / n_bins
    total = len(velocities)
    
    # Bin counts
    bins = [0] * n_bins
    for v in velocities:
        if v == v_max:
            idx = n_bins - 1
        else:
            idx = int((v - v_min) / w)
            if idx < 0: idx = 0
            if idx >= n_bins: idx = n_bins - 1
        bins[idx] += 1
    
    # Bisection for median
    def cdf(val):
        return sum(1 for v in velocities if v <= val) / total
    
    lo, hi = v_min, v_max
    for _ in range(100):
        mid = (lo + hi) / 2
        if hi - lo < 1e-9:
            break
        if cdf(mid) < 0.5:
            lo = mid
        else:
            hi = mid
    v_med = (lo + hi) / 2
    
    # Which bin contains v_med?
    if v_med == v_max:
        med_bin = n_bins - 1
    else:
        med_bin = int((v_med - v_min) / w)
        if med_bin < 0: med_bin = 0
        if med_bin >= n_bins: med_bin = n_bins - 1
    
    lines = []
    lines.append(f'v_min={v_min:.6f}')
    lines.append(f'v_max={v_max:.6f}')
    lines.append(f'bins={",".join(str(b) for b in bins)}')
    lines.append(f'v_med={v_med:.9f}')
    lines.append(f'med_bin={med_bin}')
    return '\n'.join(lines) + '\n'


def test_result_exact():
    p = Path('/output/result.txt')
    assert p.exists(), '/output/result.txt not found'
    expected = compute_expected()
    actual = p.read_text()
    assert actual == expected, f'Mismatch.\nExpected:\n{expected}\nActual:\n{actual}'
