import sys
import json
import time
import hashlib
import os
import signal
import jwt
import websocket
import logging
from functools import lru_cache
from config import settings
from util import get_private_key


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("superlaser.ingestion")


# lru_cache ensures your Ed25519 key is parsed/loaded from disk ONCE
# and served from memory for all subsequent connection/subscription frames.
@lru_cache(maxsize=1)
def get_cached_private_key():
    logger.info("Loading private key (cached for future operations)...")
    return get_private_key()


def sign_websocket_message(message: dict) -> dict:
    """Signs a WS subscription frame payload using the cached Ed25519 key."""
    private_key = get_cached_private_key()
    payload = {
        "iss": "coinbase-cloud",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "sub": settings.coinbase_key_id,
    }
    headers = {
        "kid": settings.coinbase_key_id,
        "nonce": hashlib.sha256(os.urandom(16)).hexdigest()
    }
    token = jwt.encode(payload, private_key, algorithm="EdDSA", headers=headers)
    message['jwt'] = token
    return message


class SuperlaserIngestionService:
    def __init__(self, products: list[str], channels: list[str]):
        self.products = products
        self.channels = channels  # Fixed typo: changed from self.channel to match signature
        self.ws = None
        self.running = True

        self.msg_count_mod5k = 0
        self.last_metrics_report = time.time()

        # Handle system termination signals cleanly
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def on_message(self, ws, message):
        """Main hot-path data ingestion pipeline endpoint."""
        self.msg_count_mod5k += 1
        
        if self.msg_count_mod5k % 5000 == 0:
            now = time.time()
            elapsed = now - self.last_metrics_report
            rate = self.msg_count_mod5k / elapsed
            logger.info(f"Processed {self.msg_count_mod5k} messages in {elapsed:.2f}s ({rate:.2f} msg/s)")

            self.msg_count_mod5k = 0
            self.last_metrics_report = now

        try:
            data = json.loads(message)
            
            # TODO: Direct hands-off handoff to your queue, DB, or pipeline
            print(message + "\n")

        except json.JSONDecodeError:
            logger.error("Failed to parse incoming WebSocket frame as JSON.")

    def on_open(self, ws):
        """Fires when socket connects; performs signed subscriptions in a loop."""
        logger.info(f"Connected to Coinbase WebSocket. Subscribing to: {self.channels}...")
        
        for channel in self.channels:
            payload = {
                "type": "subscribe",
                "channel": channel,
                "product_ids": self.products
            }
            try:
                ws.send(json.dumps(sign_websocket_message(payload)))
                logger.info(f"Subscription request sent for channel: '{channel}'")
            except Exception as e:
                logger.error(f"Failed to send subscription for '{channel}': {e}")

    def on_error(self, ws, error):
        logger.error(f"WebSocket Error: {error}", exc_info=True)

    def on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"WebSocket Closed. Code: {close_status_code} | Msg: {close_msg}")

    def handle_shutdown(self, signum, frame):
        """Gracefully unsubscribes from feeds in a loop and exits."""
        if not self.running:
            return
        
        logger.info(f"Received termination signal ({signum}). Initiating clean shutdown...")
        self.running = False

        if self.ws and self.ws.sock and self.ws.sock.connected:
            logger.info("Unsubscribing from active feeds...")
            try:
                for channel in self.channels:
                    payload = {
                        "type": "unsubscribe",
                        "channel": channel,
                        "product_ids": self.products
                    }
                    self.ws.send(json.dumps(sign_websocket_message(payload)))
                time.sleep(0.5)  # Pause to let frames send
            except Exception as e:
                logger.error(f"Failed to unsubscribe cleanly during shutdown: {e}")
            finally:
                logger.info("Closing active socket connection...")
                self.ws.close()
        
        logger.info("Service stopped cleanly.")

    def start(self):
        """Starts the connection loop with automatic reconnection."""
        logger.info("Booting Superlaser Ingestion Service...")
        
        while self.running:
            try:
                self.ws = websocket.WebSocketApp(
                    settings.ws_api_url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close
                )
                self.ws.run_forever(ping_interval=10, ping_timeout=5)
            except Exception as e:
                logger.error(f"Active connection dropped due to: {e}")
            
            if self.running:
                logger.info("Connection lost. Reconnecting in 5 seconds...")
                time.sleep(5)


def main():
    if not settings.coinbase_key_id or not settings.coinbase_private_key:
        logger.critical(
            "COINBASE_KEY_ID and COINBASE_PRIVATE_KEY must be "
            "provided in your .env configuration."
        )
        sys.exit(1)

    # Note: To prevent Coinbase from closing idle feeds during periods of
    # low trade volume, include the "heartbeats" channel in the list below.
    service = SuperlaserIngestionService(
        products=["BTC-USD"],
        channels=[
            "level2",
            "heartbeats",
        ]
    )

    service.start()

if __name__ == "__main__":
    main()