import os
import time
from pyngrok import ngrok

NGROK_TOKEN = "37TLhWloCKJFgf8kwude1lc9ECR_5wYYPYd74PmmXGUpzbnzw"
if not NGROK_TOKEN:
    raise RuntimeError("Set NGROK_AUTHTOKEN first")

ngrok.set_auth_token(NGROK_TOKEN)

# Create tunnel
tunnel = ngrok.connect(8000, "http")
print("Public URL:", tunnel.public_url)
print("Press CTRL+C to stop.")

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    print("Stopping tunnel...")
    ngrok.disconnect(tunnel.public_url)
    ngrok.kill()
