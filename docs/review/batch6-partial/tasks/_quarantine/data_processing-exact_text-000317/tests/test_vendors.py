from pathlib import Path
import yaml

EXPECTED = """- vendor_id: V001
  name: Acme Corp
  category: widgets
  price: '10.00'
- vendor_id: V002
  name: Beta Ltd
  category: gadgets
  price: '20.00'
- vendor_id: V004
  name: Delta Inc
  category: parts
  price: '15.00'
- vendor_id: V005
  name: Echo LLC
  category: widgets
  price: '8.50'
"""

def test_vendors_yaml():
    p = Path('/output/vendors.yaml')
    assert p.exists(), '/output/vendors.yaml not found'
    assert p.read_text() == EXPECTED
