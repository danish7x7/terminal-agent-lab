```bash
cat > /app/server.py << 'EOF'
import bz2, csv
from flask import Flask, Response
import yaml

app = Flask(__name__)

def process():
    with bz2.open('/data/vendors.bz2', 'rt') as f:
        reader = csv.DictReader(f, delimiter='|')
        seen = {}
        for row in reader:
            vid = row.get('vendor_id','').strip()
            name = row.get('name','').strip()
            if not vid or not name:
                continue
            if vid not in seen:
                seen[vid] = {'vendor_id': vid, 'name': name, 'category': row['category'].strip(), 'price': row['price'].strip()}
    return [seen[k] for k in sorted(seen)]

@app.route('/vendors')
def vendors():
    records = process()
    out = yaml.dump(records, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return Response(out, mimetype='text/plain')

if __name__ == '__main__':
    app.run(port=7654)
EOF
python /app/server.py &
sleep 2
curl -s http://localhost:7654/vendors > /output/vendors.yaml
```
