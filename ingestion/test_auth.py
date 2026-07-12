# superlaser/ingestion/test_auth.py
import time
import jwt
import hashlib
import os
import base64
import requests
from cryptography.hazmat.primitives.asymmetric import ed25519
from config import settings

def generate_test_jwt(method: str, host: str, path: str) -> str:
    """Decodes raw Ed25519 base64 private key bytes and signs an EdDSA REST token."""
    # Ensure whitespaces or formatting fragments are stripped clean
    clean_b64 = settings.coinbase_private_key.strip().replace("\n", "").replace("\\n", "")
    raw_key_bytes = base64.b64decode(clean_b64)
    
    # Instantiate your 32-byte private key seed natively
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(raw_key_bytes[:32])
    
    payload = {
        "iss": "cdp",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 60,  # Valid for 60 seconds
        "sub": settings.coinbase_key_id,
        "uri": f"{method} {host}{path}" # Bound explicitly to the specific REST request signature
    }
    
    headers = {
        "kid": settings.coinbase_key_id,
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest()
    }
    
    return jwt.encode(payload, private_key, algorithm="EdDSA", headers=headers)

def run_verification():
    """Executes an inline programmatic network test against the portfolios collection."""
    method = "GET"
    host = "api.coinbase.com"
    path = "/api/v3/brokerage/portfolios"
    url = f"https://{host}{path}"
    
    print("🚀 Instantiating local cryptographic verification engine...")
    try:
        # 1. Compute the time-bound token in memory
        token = generate_test_jwt(method, host, path)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 2. Fire the network request natively inside python
        print(f"📡 Querying Coinbase Advanced Trade gateway -> {url}")
        response = requests.get(url, headers=headers)
        
        # 3. Assert response state
        if response.status_code == 200:
            print("✅ Connection Verified! Credentials are 100% accurate.")
            print(f"📦 Response Payload: {response.text}")
        else:
            print(f"❌ Verification Fault: Status Code {response.status_code}")
            print(f"🚨 Remote Feedback: {response.text}")
            
    except Exception as e:
        print(f"💥 Runtime Exception: {e}")

if __name__ == "__main__":
    run_verification()