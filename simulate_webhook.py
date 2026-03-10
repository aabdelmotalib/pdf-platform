
import hmac
import hashlib
import json
import requests
from datetime import datetime

# Settings
BASE_URL = "http://localhost:8000"
HMAC_SECRET = "F2A3E1FEE24EA0A2D342D7CFEF28BA39"
GATEWAY_REF = "999888777" # Matches current pending payment if we create one, or just manually set

def generate_signed_payload(obj_data, secret):
    fields = [
        "amount_cents", "created_at", "currency", "error_occured",
        "has_parent_transaction", "id", "integration_id", "is_3d_secure",
        "is_auth", "is_capture", "is_refunded", "is_standalone_payment",
        "is_voided", "order", "owner", "pending",
        "source_data.pan", "source_data.sub_type", "source_data.type",
        "success"
    ]
    
    concat = ""
    for field in fields:
        if "." in field:
            parts = field.split(".")
            val = obj_data.get(parts[0], {}).get(parts[1], "")
        else:
            val = obj_data.get(field, "")
        
        if isinstance(val, bool):
            concat += str(val).lower()
        else:
            concat += str(val if val is not None else "")
            
    return hmac.new(
        secret.encode(),
        concat.encode(),
        hashlib.sha512
    ).hexdigest()

def simulate_webhook():
    # 1. Create a pending payment manually in logic if needed, 
    # but we can just use the one we attempted earlier if it was created.
    # Actually, I'll just check the DB for the last pending payment gateway_ref.
    
    # Payload structure
    obj = {
        "id": 12345,
        "amount_cents": 1000, # 10.00 EGP
        "success": True,
        "created_at": "2026-03-10T05:00:00.000000",
        "currency": "EGP",
        "error_occured": False,
        "has_parent_transaction": False,
        "integration_id": 5569576,
        "is_3d_secure": True,
        "is_auth": False,
        "is_capture": True,
        "is_refunded": False,
        "is_standalone_payment": True,
        "is_voided": False,
        "order": {"id": 999888777},
        "owner": 1,
        "pending": False,
        "source_data": {
            "pan": "2345",
            "sub_type": "MasterCard",
            "type": "card"
        }
    }
    
    payload = {"obj": obj}
    hmac_val = generate_signed_payload(obj, HMAC_SECRET)
    
    print(f"Sending simulated webhook (gateway_ref=999888777, hmac={hmac_val[:10]}...)...")
    res = requests.post(f"{BASE_URL}/payments/webhook?hmac={hmac_val}", json=payload)
    print(f"Response: {res.status_code} - {res.text}")

if __name__ == "__main__":
    simulate_webhook()
