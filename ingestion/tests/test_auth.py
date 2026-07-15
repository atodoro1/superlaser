import requests

from util import generate_jwt


def run_verification():
    """https://docs.cdp.coinbase.com/get-started/authentication/jwt-authentication#using-a-jwt"""
    method = "GET"
    host = "api.coinbase.com"
    path = "/api/v3/brokerage/portfolios"
    url = f"https://{host}{path}"

    print("Generating test JWT...")
    try:
        token = generate_jwt(method, host, path)
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print(f"Sending request to {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print("Connection Verified! Credentials are 100% accurate.")
            print(f"Response Payload: {response.text}")
        else:
            print(f"Verification Fault: Status Code {response.status_code}")
            print(f"Remote Feedback: {response.text}")
            
    except Exception as e:
        print(f"Runtime Exception: {e}")

if __name__ == "__main__":
    run_verification()