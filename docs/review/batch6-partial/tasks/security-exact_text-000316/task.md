You are a developer investigating a flagged security token system. The file `/challenge/token.hex` contains an AES-128-CBC encrypted blob (hex-encoded, IV is 16 zero bytes). The AES key is a 4-digit PIN (0000–9999) zero-padded on the right to 16 bytes (ASCII). Brute-force the PIN to decrypt the blob.

The decrypted plaintext is a base64-encoded string. Decode it to obtain a message of the form:

```
DATA:<payload>\nSIG:<hex_signature>
```

Verify the RSA signature (`SHA-256` digest, PKCS#1 v1.5) on `<payload>` (UTF-8 bytes) using the public key in `/challenge/pubkey.pem`. If the signature is valid, write exactly the value of `<payload>` followed by a single newline to `/output/result.txt`.