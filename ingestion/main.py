import time
import json
import jwt
import hashlib
import os
import websocket
import threading
from datetime import datetime
from config import settings

ALGORITHM = "ES256"

def sign_with_jwt(message):
    """Generates the required JWT authentication mapping for Coinbase Advanced Trade."""
    payload = {
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "sub": settings.api_key,
    }
    headers = {
        "kid": settings.api_key,
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest()
    }
    token = jwt.encode(payload, settings.signing_key, algorithm=ALGORITHM, headers=headers)
    message['jwt'] = token
    return message

def send_action(ws, action_type: str, channel_name: str, products: list):
    """Handles both subscribe and unsubscribe payloads cleanly."""
    message = {
        "type": action_type,
        "channel": channel_name,
        "product_ids": products
    }
    signed_message = sign_with_jwt(message)
    ws.send(json.dumps(signed_message))

def on_message(ws, message):
    data = json.loads(message)
    print(f"Received raw frame: {data.get('channel')} - {data.get('type')}")

def on_open(ws):
    print("WebSocket connection established.")
    products = ["BTC-USD"]
    
    # Best Practice: Always subscribe to heartbeats alongside your data channel
    send_action(ws, "subscribe", "heartbeats", products)
    send_action(ws, "subscribe", "level2", products)

def start_websocket():
    # ping_interval=30 automatically sends low-level ping frames in the background
    ws = websocket.WebSocketApp(
        settings.ws_api_url, 
        on_open=on_open, 
        on_message=on_message
    )
    ws.run_forever(ping_interval=30, ping_timeout=10)

def main():
    # Run the websocket loop inside a background thread so your main thread stays free
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()

    start_time = datetime.utcnow()
    sent_unsub = False

    try:
        while True:
            # Simple demonstration to trigger an unsubscribe action after 10 seconds
            if (datetime.utcnow() - start_time).total_seconds() > 10 and not sent_unsub:
                print("Triggering programmatic unsubscribe for level2...")
                
                # To send a message from outside the thread loop, open a quick temp socket
                temp_ws = websocket.create_connection(settings.ws_api_url)
                send_action(temp_ws, "unsubscribe", "level2", ["BTC-USD"])
                temp_ws.close()
                
                sent_unsub = True
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down ingestion service.")

if __name__ == "__main__":
    main()
