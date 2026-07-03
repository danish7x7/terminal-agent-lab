## Damped Oscillator Analysis

Position samples from a damped harmonic oscillator are stored in `/data/oscillator.csv` (columns: `t`, `x`). The true model is `x(t) = A * exp(-gamma*t) * cos(omega*t + phi)`.

Run the following analysis pipeline and write results to `/output/results.txt`, one floating-point number per line (6 significant figures), in this exact order:

1. **Fitted omega** — fit the data to `A*exp(-gamma*t)*cos(omega*t+phi)` using nonlinear least squares (`scipy.optimize.curve_fit`); report the fitted `omega`.
2. **Fitted gamma** — report the fitted decay constant `gamma`.
3. **Mean kinetic energy** — numerically differentiate `x(t)` (using `np.gradient(x, t)`, assuming unit mass) to get velocity `v(t)`, then compute the mean of `0.5*v^2` over all interior points (excluding first and last).
4. **Total energy dissipated** — using your velocity estimates, compute the power loss magnitude `2*gamma_fit * 0.5 * v(t)^2` at each point, then integrate using the trapezoidal rule over the full time range.
5. **Histogram peak bin center** — bin the instantaneous kinetic energy values `0.5*v(t)^2` (interior points only) into 20 equal-width bins over `[0, max_ke]`; report the center of the bin with the highest count.
6. **Linear system solution norm** — form the 4×4 system `V @ c = b` where `V[i,j] = t_i^j` for `i,j in 0..3` using the first 4 time points, and `b[i] = x(t_i)`; solve for `c` and report `norm(c)` (L2 norm).

Write exactly 6 lines to `/output/results.txt`, each a floating-point number with 6 significant figures (e.g., `3.14159`).
