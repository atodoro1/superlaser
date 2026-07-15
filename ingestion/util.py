import time
import jwt
import hashlib
import os
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from config import settings


def generate_jwt(method: str, host: str, path: str) -> str:
    """Decodes raw Ed25519 base64 private key bytes and signs an EdDSA REST token."""
    # Ensure whitespaces or formatting fragments are stripped clean
    clean_b64 = settings.coinbase_private_key.strip().replace("\n", "").replace("\\n", "")
    raw_key_bytes = base64.b64decode(clean_b64)
    
    # Instantiate your 32-byte private key seed natively
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw_key_bytes[:32])
    
    # https://docs.cdp.coinbase.com/get-started/authentication/jwt-authentication#code-samples-for-ed25519-keys
    # The Ruby example is a good reference for how to structure the payload and headers for JWT signing
    payload = {
        "sub": settings.coinbase_key_id,
        "iss": "cdp",
        "aud": "cdp_service",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 60,
        "uri": f"{method} {host}{path}"
    }
    
    headers = {
        "alg": "EdDSA",
        "typ": "JWT",
        "kid": settings.coinbase_key_id,
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest()
    }
    
    return jwt.encode(payload, private_key, algorithm="EdDSA", headers=headers)