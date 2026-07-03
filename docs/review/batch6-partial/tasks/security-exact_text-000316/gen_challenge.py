from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import base64, os

# Fixed PIN
PIN = '6183'
key = PIN.encode().ljust(16, b'\x00')
iv = b'\x00' * 16

# RSA key pair (fixed seed via deterministic generation not possible, use fixed private key bytes)
# Generate and save private key
from cryptography.hazmat.backends import default_backend
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

# Save public key
pubkey_pem = private_key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
with open('/challenge/pubkey.pem', 'wb') as f:
    f.write(pubkey_pem)

# Sign payload
payload = 'SECURE_PAYLOAD_d4e9b2f1'
sig = private_key.sign(payload.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())

# Build message
msg = f'DATA:{payload}\nSIG:{sig.hex()}'
msg_b64 = base64.b64encode(msg.encode('ascii')).decode('ascii')

# PKCS7 pad and encrypt
plaintext = msg_b64.encode('ascii')
pad_len = 16 - (len(plaintext) % 16)
plaintext += bytes([pad_len] * pad_len)
cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
enc = cipher.encryptor()
ciphertext = enc.update(plaintext) + enc.finalize()

with open('/challenge/token.hex', 'w') as f:
    f.write(ciphertext.hex())

print('Challenge generated. PIN:', PIN)
