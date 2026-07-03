```bash
mkdir -p /output
cat > /app/analyze.py << 'PY'
import numpy as np
from scipy.optimize import curve_fit
from scipy.linalg import solve

data = np.loadtxt('/data/oscillator.csv', delimiter=',', skiprows=1)
t = data[:, 0]
x = data[:, 1]

# 1 & 2: Fit damped cosine
def model(t, A, gamma, omega, phi):
    return A * np.exp(-gamma * t) * np.cos(omega * t + phi)

p0 = [2.0, 0.3, 6.28, 0.5]
popt, _ = curve_fit(model, t, x, p0=p0, maxfev=10000)
A_fit, gamma_fit, omega_fit, phi_fit = popt
print(f'Fitted: A={A_fit:.4f}, gamma={gamma_fit:.6f}, omega={omega_fit:.6f}, phi={phi_fit:.4f}')

# 3: Numerical differentiation -> velocity -> mean KE (interior points)
v = np.gradient(x, t)
ke = 0.5 * v**2
mean_ke = np.mean(ke[1:-1])
print(f'Mean KE: {mean_ke:.6f}')

# 4: Total energy dissipated via trapezoidal integration
power_loss = 2 * gamma_fit * ke  # |power| = 2*gamma * 0.5*v^2
total_dissipated = np.trapz(power_loss, t)
print(f'Total dissipated: {total_dissipated:.6f}')

# 5: Histogram of KE (interior points), find peak bin center
ke_interior = ke[1:-1]
counts, bin_edges = np.histogram(ke_interior, bins=20, range=(0, ke_interior.max()))
peak_idx = np.argmax(counts)
peak_center = 0.5 * (bin_edges[peak_idx] + bin_edges[peak_idx + 1])
print(f'Peak bin center: {peak_center:.6f}')

# 6: Vandermonde system with first 4 points
t4 = t[:4]
x4 = x[:4]
V = np.array([[t4[i]**j for j in range(4)] for i in range(4)])
c = solve(V, x4)
c_norm = np.linalg.norm(c)
print(f'c norm: {c_norm:.6f}')

results = [omega_fit, gamma_fit, mean_ke, total_dissipated, peak_center, c_norm]
with open('/output/results.txt', 'w') as f:
    for r in results:
        f.write(f'{r:.6g}\n')

print('Results written:')
for i, r in enumerate(results):
    print(f'  {i+1}: {r:.6g}')
PY
python3 /app/analyze.py
```