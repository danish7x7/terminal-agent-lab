```bash
python3 - <<'EOF'
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import base64, binascii

ciphertext = bytes.fromhex(open('/challenge/token.hex').read().strip())
iv = b'\x00' * 16

for pin in range(10000):
    key = str(pin).zfill(4).encode().ljust(16, b'\x00')
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    dec = cipher.decryptor()
    pt = dec.update(ciphertext) + dec.finalize()
    try:
        text = pt.rstrip(b'\x00').rstrip(b'\x10').decode('ascii')
        # strip PKCS7 padding
        pad_len = pt[-1]
        if 1 <= pad_len <= 16:
            pt2 = pt[:-pad_len]
        else:
            continue
        text = pt2.decode('ascii')
        decoded = base64.b64decode(text)
        msg = decoded.decode('ascii')
        if msg.startswith('DATA:') and '\nSIG:' in msg:
            data_part, sig_part = msg.split('\nSIG:')
            payload = data_part[len('DATA:'):]
            sig = bytes.fromhex(sig_part)
            pubkey_pem = open('/challenge/pubkey.pem','rb').read()
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            pubkey = load_pem_public_key(pubkey_pem)
            pubkey.verify(sig, payload.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
            with open('/output/result.txt','w') as f:
                f.write(payload + '\n')
            print('PIN:', str(pin).zfill(4), 'Payload:', payload)
            break
    except Exception:
        continue
EOF
```
