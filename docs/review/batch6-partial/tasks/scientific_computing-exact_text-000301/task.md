# Damped Oscillator Simulation Pipeline

I'm running a damped harmonic oscillator simulation and need to analyze the velocity distribution.

## Setup

Write a Go HTTP server at `/app/simserver/main.go` that listens on port 8731. It must handle `GET /simulate` with query parameters:
- `omega0` — natural frequency (float)
- `gamma` — damping coefficient (float)
- `x0` — initial position (float)
- `v0` — initial velocity (float)
- `dt` — time step (float)
- `steps` — number of RK4 steps (int)

The server returns a JSON array of objects `[{"t":...,"x":...,"v":...}, ...]` — one entry per step including the initial state, using **4th-order Runge-Kutta** on `dx/dt = v`, `dv/dt = -gamma*v - omega0^2*x`.

## Simulation

Query the server with: `omega0=2.0`, `gamma=0.5`, `x0=1.0`, `v0=0.0`, `dt=0.01`, `steps=2000`.

## Analysis

1. Extract all **velocity** values from the response (2001 values: indices 0..2000).
2. Compute `v_min = min(velocities)`, `v_max = max(velocities)`.
3. Bin the velocities into **20 equal-width bins** spanning `[v_min, v_max]`. Each bin `i` covers `[v_min + i*w, v_min + (i+1)*w)` where `w = (v_max - v_min) / 20`. The last bin is closed on the right.
4. Using **bisection**, find the velocity value `v_med` in `[v_min, v_max]` such that the fraction of velocity samples `<= v_med` equals exactly **0.5** (i.e., find the median). Use the empirical CDF (count of samples <= v) / total_samples. Run bisection until the interval width is less than `1e-9`.
5. Determine which bin index (0-based) contains `v_med`.

## Output

Write `/output/result.txt` with exactly this format (no extra whitespace, trailing newline):

```
v_min=<V_MIN>
v_max=<V_MAX>
bins=<B0>,<B1>,...,<B19>
v_med=<V_MED>
med_bin=<IDX>
```

Where:
- `<V_MIN>` and `<V_MAX>` are formatted with **6 decimal places**
- `<Bi>` are the 20 bin counts as integers separated by commas
- `<V_MED>` is formatted with **9 decimal places**
- `<IDX>` is the 0-based bin index containing `v_med`
