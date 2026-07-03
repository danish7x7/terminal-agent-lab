```bash
# 1. Write the Go server
mkdir -p /app/simserver
cat > /app/simserver/main.go << 'GOEOF'
package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
)

type State struct {
	T float64 `json:"t"`
	X float64 `json:"x"`
	V float64 `json:"v"`
}

func simulate(omega0, gamma, x0, v0, dt float64, steps int) []State {
	results := make([]State, 0, steps+1)
	x, v, t := x0, v0, 0.0
	results = append(results, State{t, x, v})
	f := func(xi, vi float64) (float64, float64) {
		return vi, -gamma*vi - omega0*omega0*xi
	}
	for i := 0; i < steps; i++ {
		k1x, k1v := f(x, v)
		k2x, k2v := f(x+dt/2*k1x, v+dt/2*k1v)
		k3x, k3v := f(x+dt/2*k2x, v+dt/2*k2v)
		k4x, k4v := f(x+dt*k3x, v+dt*k3v)
		x = x + dt/6*(k1x+2*k2x+2*k3x+k4x)
		v = v + dt/6*(k1v+2*k2v+2*k3v+k4v)
		t += dt
		results = append(results, State{t, x, v})
	}
	return results
}

func handler(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	omega0, _ := strconv.ParseFloat(q.Get("omega0"), 64)
	gamma, _ := strconv.ParseFloat(q.Get("gamma"), 64)
	x0, _ := strconv.ParseFloat(q.Get("x0"), 64)
	v0, _ := strconv.ParseFloat(q.Get("v0"), 64)
	dt, _ := strconv.ParseFloat(q.Get("dt"), 64)
	steps, _ := strconv.Atoi(q.Get("steps"))
	results := simulate(omega0, gamma, x0, v0, dt, steps)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func main() {
	http.HandleFunc("/simulate", handler)
	fmt.Println("Listening on :8731")
	http.ListenAndServe(":8731", nil)
}
GOEOF

# 2. Build and run the server
cd /app/simserver
go build -o simserver main.go
./simserver &
SERVER_PID=$!
sleep 2

# 3. Query the server
curl -s "http://localhost:8731/simulate?omega0=2.0&gamma=0.5&x0=1.0&v0=0.0&dt=0.01&steps=2000" > /tmp/traj.json

# 4. Process in Python
python3 << 'PYEOF'
import json, math

with open('/tmp/traj.json') as f:
    data = json.load(f)

velocities = [d['v'] for d in data]

v_min = min(velocities)
v_max = max(velocities)
n_bins = 20
w = (v_max - v_min) / n_bins
total = len(velocities)

bins = [0] * n_bins
for v in velocities:
    if v == v_max:
        idx = n_bins - 1
    else:
        idx = int((v - v_min) / w)
        if idx < 0: idx = 0
        if idx >= n_bins: idx = n_bins - 1
    bins[idx] += 1

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

with open('/output/result.txt', 'w') as f:
    f.write('\n'.join(lines) + '\n')

print('Done. Result written to /output/result.txt')
PYEOF

# 5. Stop server
kill $SERVER_PID 2>/dev/null || true
```
