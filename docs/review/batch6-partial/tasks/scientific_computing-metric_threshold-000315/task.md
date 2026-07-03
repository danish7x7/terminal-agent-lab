# ODE Stepper Signal-Processing Pipeline

You are building a numerical pipeline that combines ODE integration, FFT-based signal filtering, and root finding. Work through the following steps and write your results to `/output/results.txt`.

## Background

You are given a noisy time-series signal stored in `/data/signal.csv` (columns: `t,y`), sampled at 512 equally-spaced points over `[0, 2π]`. The signal is a superposition of a low-frequency component plus high-frequency noise.

## Your Pipeline Tasks

### Stage 1 – FFT Low-Pass Filter
Load `/data/signal.csv`. Apply an FFT-based low-pass filter that **keeps only frequency components with index ≤ 8** (zero out all higher-frequency components in both positive and negative halves), then inverse-FFT to recover the cleaned signal `y_clean`.

### Stage 2 – Fit a Smooth Reference via RK4 ODE Stepper
The clean signal should approximate the solution of the IVP:
```
 dy/dt = -0.5 * y + A * cos(t),   y(0) = y_clean[0]
```
where `A` is unknown. Use a **bisection root-finder** (on the interval `A ∈ [0.1, 5.0]`) to find the value of `A` such that the L2 norm of `(y_ode(t) - y_clean)` is minimised — specifically, find `A*` where the **derivative of the L2 norm with respect to A changes sign**, i.e., solve
```
 f(A) = dot(y_ode(A) - y_clean, d_y_ode/dA) = 0
```
Approximate `d_y_ode/dA` by finite difference with `dA = 1e-4`. Integrate the ODE using **RK4** with the same 512 time-points. Use bisection with **tolerance 1e-6**.

### Stage 3 – Compute Residual Norms
With the best-fit `A*`:
- Compute `r = y_ode(A*) - y_clean` (512-element vector)
- Compute `norm_L2 = ||r||_2`, `norm_L1 = ||r||_1`, `norm_Linf = ||r||_inf`

### Output
Write `/output/results.txt` with **exactly 4 lines**:
```
A_star=<value rounded to 6 decimal places>
norm_L2=<value rounded to 6 decimal places>
norm_L1=<value rounded to 6 decimal places>
norm_Linf=<value rounded to 6 decimal places>
```
Example format (values are illustrative):
```
A_star=1.234567
norm_L2=0.012345
norm_L1=0.123456
norm_Linf=0.001234
```