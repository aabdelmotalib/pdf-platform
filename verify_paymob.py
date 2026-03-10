
import requests
import json

BASE_URL = "http://localhost:8000"
EMAIL = "testuser-1773112457276409074@example.com"
PASSWORD = "TestPass123!"

def test_payment_flow():
    # 1. Login
    print("Logging in...")
    login_res = requests.post(f"{BASE_URL}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    login_res.raise_for_status()
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Initiate Payment
    print("Initiating payment...")
    init_res = requests.post(
        f"{BASE_URL}/payments/initiate", 
        json={"plan_id": 2, "method": "card"},
        headers=headers
    )
    print(f"Initiation Response Status: {init_res.status_code}")
    if init_res.status_code == 200:
        print(json.dumps(init_res.json(), indent=2))
        payment_id = init_res.json()["payment_id"]
        order_id = init_res.json()["order_id"]
    else:
        print(init_res.text)
        return

    # 3. Check History
    print("\nChecking payment history...")
    history_res = requests.get(f"{BASE_URL}/payments/history", headers=headers)
    history_res.raise_for_status()
    print(json.dumps(history_res.json(), indent=2))

    # 4. Check Status
    print(f"\nChecking status for payment {payment_id}...")
    status_res = requests.get(f"{BASE_URL}/payments/{payment_id}/status", headers=headers)
    status_res.raise_for_status()
    print(json.dumps(status_res.json(), indent=2))

if __name__ == "__main__":
    try:
        test_payment_flow()
    except Exception as e:
        print(f"Error: {e}")
