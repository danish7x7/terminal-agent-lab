FROM python:3.11-slim
RUN pip install --no-cache-dir numpy scipy pytest
RUN python3 -c "
import numpy as np
t = np.linspace(0, 10, 500)
A, gamma, omega, phi = 2.0, 0.3, 2.0*3.14159265358979, 0.5
x = A * np.exp(-gamma*t) * np.cos(omega*t + phi)
import csv
with open('/data/oscillator.csv','w',newline='') as f:
    w = csv.writer(f)
    w.writerow(['t','x'])
    for ti,xi in zip(t,x):
        w.writerow([f'{ti:.8f}', f'{xi:.8f}'])
" 2>/dev/null || true
RUN mkdir -p /data /output
RUN python3 << 'PYEOF'
import numpy as np
t = np.linspace(0, 10, 500)
A, gamma, omega, phi = 2.0, 0.3, 2.0*3.14159265358979, 0.5
x = A * np.exp(-gamma*t) * np.cos(omega*t + phi)
import csv
with open('/data/oscillator.csv','w',newline='') as f:
    w = csv.writer(f)
    w.writerow(['t','x'])
    for ti,xi in zip(t,x):
        w.writerow([f'{ti:.8f}', f'{xi:.8f}'])
PYEOF
WORKDIR /app
