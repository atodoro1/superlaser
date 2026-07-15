# ingestion/main.py
import sys
import json
import time
import hashlib
import os
import signal
import jwt
import websocket
from config import settings
from util import get_private_key


def sign_websocket_message(message: dict) -> dict:
    """Signs a WS subscription frame payload using the Ed25519 key."""
    private_key = get_private_key()
    payload = {
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "sub": settings.coinbase_key_id,
    }
    headers = {
        "alg": "EdDSA",
        "kid": settings.coinbase_key_id,
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest()
    }
    token = jwt.encode(payload, private_key, algorithm="EdDSA", headers=headers)
    message['jwt'] = token
    return message


class SuperlaserIngestionService:
    def __init__(self, products: list[str], channel: str):
        self.products = products
        self.channel = channel
        self.ws = None
        self.running = True

        # Handle system termination signals cleanly
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def on_message(self, ws, message):
        """Main data ingestion pipeline endpoint."""
        data = json.loads(message)
        
        # TODO: Handle actual ingestion logic (e.g., pipeline, DB, etc.)
        print(json.dumps(data) + "\n")

    def on_open(self, ws):
        """Fires when socket connects; performs signed subscription."""
        print(f"Connected to Coinbase WebSocket. Subscribing to '{self.channel}'...")
        message = {
            "type": "subscribe",
            "channel": self.channel,
            "product_ids": self.products
        }
        signed_message = sign_websocket_message(message)
        ws.send(json.dumps(signed_message))

    def on_error(self, ws, error):
        print(f"WS Error: {error}", file=sys.stderr)

    def on_close(self, ws, close_status_code, close_msg):
        print(f"WS Closed. Code: {close_status_code}, Msg: {close_msg}")

    def handle_shutdown(self, signum, frame):
        """Gracefully unsubscribes from feed on the active socket and exits."""
        if not self.running:
            return
        
        print(f"\nReceived termination signal ({signum}). Shutting down cleanly...")
        self.running = False

        if self.ws and self.ws.sock and self.ws.sock.connected:
            print("Sending unsubscribe payload...")
            message = {
                "type": "unsubscribe",
                "channel": self.channel,
                "product_ids": self.products
            }
            try:
                signed_message = sign_websocket_message(message)
                self.ws.send(json.dumps(signed_message))
                time.sleep(0.5)  # Pause to let frame send
            except Exception as e:
                print(f"Failed to unsubscribe: {e}", file=sys.stderr)
            finally:
                print("Closing socket connections...")
                self.ws.close()
        
        print("Service stopped cleanly.")
        sys.exit(0)

    def start(self):
        """Starts the blocking connection loop."""
        self.ws = websocket.WebSocketApp(
            settings.ws_api_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        # Built-in WS heartbeats keep the connection alive
        self.ws.run_forever(ping_interval=10, ping_timeout=5)


def main():
    if not settings.coinbase_key_id or not settings.coinbase_private_key:
        print(
            "CRITICAL: COINBASE_KEY_ID and COINBASE_PRIVATE_KEY must be "
            "provided in your .env configuration.",
            file=sys.stderr
        )
        sys.exit(1)

    # Initialize and boot daemon
    service = SuperlaserIngestionService(
        products=["BTC-USD"],
        channel="level2"
    )

    print("Booting Superlaser Ingestion Service...")
    service.start()

if __name__ == "__main__":
    main()