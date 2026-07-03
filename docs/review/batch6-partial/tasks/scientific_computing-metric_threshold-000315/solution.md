```bash
cat > /app/solve.py <<'PYEOF'
import numpy as np
import csv

# Load signal
ts, ys = [], []
with open('/data/signal.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ts.append(float(row['t']))
        ys.append(float(row['y']))

t = np.array(ts)
y = np.array(ys)
N = len(t)

# Stage 1: FFT low-pass filter, keep indices <= 8
Y = np.fft.fft(y)
Y_filt = np.zeros(N, dtype=complex)
Y_filt[:9] = Y[:9]
if N - 8 < N:
    Y_filt[N-8:] = Y[N-8:]
y_clean = np.fft.ifft(Y_filt).real

# Stage 2: RK4 integrator for dy/dt = -0.5*y + A*cos(t)
def rk4_solve(A, t, y0):
    n = len(t)
    y = np.zeros(n)
    y[0] = y0
    for i in range(n - 1):
        h = t[i+1] - t[i]
        ti = t[i]
        yi = y[i]
        k1 = -0.5 * yi + A * np.cos(ti)
        k2 = -0.5 * (yi + 0.5*h*k1) + A * np.cos(ti + 0.5*h)
        k3 = -0.5 * (yi + 0.5*h*k2) + A * np.cos(ti + 0.5*h)
        k4 = -0.5 * (yi + h*k3) + A * np.cos(ti + h)
        y[i+1] = yi + h/6.0*(k1 + 2*k2 + 2*k3 + k4)
    return y

y0 = y_clean[0]
dA = 1e-4

def f(A):
    yo = rk4_solve(A, t, y0)
    yo_p = rk4_solve(A + dA, t, y0)
    dyo_dA = (yo_p - yo) / dA
    r = yo - y_clean
    return np.dot(r, dyo_dA)

# Bisection on [0.1, 5.0]
lo, hi = 0.1, 5.0
for _ in range(100):
    mid = (lo + hi) / 2.0
    if f(mid) * f(lo) < 0:
        hi = mid
    else:
        lo = mid
    if hi - lo < 1e-6:
        break

A_star = (lo + hi) / 2.0

# Stage 3: compute norms
y_ode = rk4_solve(A_star, t, y0)
r = y_ode - y_clean
norm_L2 = np.linalg.norm(r, 2)
norm_L1 = np.linalg.norm(r, 1)
norm_Linf = np.linalg.norm(r, np.inf)

with open('/output/results.txt', 'w') as out:
    out.write(f'A_star={A_star:.6f}\n')
    out.write(f'norm_L2={norm_L2:.6f}\n')
    out.write(f'norm_L1={norm_L1:.6f}\n')
    out.write(f'norm_Linf={norm_Linf:.6f}\n')

print('Done:', A_star, norm_L2, norm_L1, norm_Linf)
PYEOF
python3 /app/solve.py
cat /output/results.txt
```