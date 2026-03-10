
import httpx
import os
import json

PAYMOB_API_KEY = "ZXlKaGJHY2lPaUpJVXpVeE1pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SmpiR0Z6Y3lJNklrMWxjbU5vWVc1MElpd2ljSEp2Wm1sc1pWOXdheUk2TVRRNE56TTVPQ3dpYm1GdFpTSTZJbWx1YVhScFlXd2lmUS5qWkxkaEFMemRoeDY1dkxzeFJVY1FOdkphS1hkdUxhQ18zb2NZX2hIREp6c0ZoMzFDN1JOeGd2cFNHOHBUelhNZGphX2Z5bTZKc0M2a2g4STV3VXEwdw=="
BASE_URL = "https://accept.paymob.com/api"

async def test_key_directly():
    url = f"{BASE_URL}/ecommerce/orders"
    payload = {
        "auth_token": PAYMOB_API_KEY,
        "delivery_needed": False,
        "amount_cents": 100,
        "currency": "EGP",
        "items": []
    }
    async with httpx.AsyncClient() as client:
        print(f"Testing create_order with key as token...")
        response = await client.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_key_directly())
