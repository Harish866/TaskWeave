import os
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv(
    "PAYPAL_BASE_URL",
    "https://api-m.sandbox.paypal.com",
).rstrip("/")


def get_paypal_access_token():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise ValueError("PayPal Sandbox credentials are missing from .env.")

    response = requests.post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        headers={"Accept": "application/json", "Accept-Language": "en_US"},
        data={"grant_type": "client_credentials"},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"PayPal authentication failed: HTTP {response.status_code}"
        )

    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("PayPal did not return an access token.")
    return token


def get_paypal_order(order_id):
    token = get_paypal_access_token()
    response = requests.get(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=20,
    )
    if not response.ok:
        raise RuntimeError(
            f"PayPal order lookup failed: HTTP {response.status_code}"
        )
    return response.json()


def capture_paypal_order(order_id):
    token = get_paypal_access_token()
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={},
        timeout=30,
    )
    if not response.ok:
        try:
            details = response.json()
        except ValueError:
            details = response.text[:1000]
        raise RuntimeError(
            f"PayPal capture failed: HTTP {response.status_code}; "
            f"details: {details}"
        )
    return response.json()
