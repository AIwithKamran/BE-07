import hmac
import hashlib
import requests

secret = "your_safepay_webhook_secret_here" # Update this if you have a webhook secret in .env!

payload = """{
  "event": "payment.success",
  "metadata": {
    "tenant_id": "1"
  }
}"""

# 1. Generate the valid signature
signature = hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()

# 2. Send the request to your local server with the signature header
response = requests.post(
    "http://127.0.0.1:8000/webhooks/safepay", 
    headers={
        "Content-Type": "application/json",
        "x-sfpy-signature": signature
    },
    data=payload
)

print(response.status_code)
print(response.json())
