from decimal import Decimal

import requests

from .paypal_client import PAYPAL_BASE_URL, get_paypal_access_token


def create_paypal_order(plan, return_url, cancel_url):
    """Create a PayPal Sandbox CAPTURE order from the server-side quote."""
    if plan.status != "APPROVED":
        raise ValueError("Only approved plans can be paid for.")

    amount = Decimal(plan.total_cost)
    if amount <= 0:
        raise ValueError("Plan amount must be greater than zero.")
    if plan.currency != "USD":
        raise ValueError("Only USD payments are supported.")

    token = get_paypal_access_token()
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": str(plan.id),
            "custom_id": f"TASKWEAVE_PLAN_{plan.id}",
            "description": f"TASKWEAVE project plan #{plan.id}",
            "amount": {
                "currency_code": plan.currency,
                "value": f"{amount:.2f}",
            },
        }],
        "payment_source": {
            "paypal": {
                "experience_context": {
                    "brand_name": "TASKWEAVE",
                    "user_action": "PAY_NOW",
                    "return_url": return_url,
                    "cancel_url": cancel_url,
                }
            }
        },
    }
    response = requests.post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": f"taskweave-plan-{plan.id}",
        },
        json=payload,
        timeout=30,
    )
    if not response.ok:
        raise RuntimeError(
            f"PayPal order creation failed: HTTP {response.status_code}; "
            f"details: {response.text[:1000]}"
        )

    order = response.json()
    approval_url = next(
        (
            link.get("href")
            for link in order.get("links", [])
            if link.get("rel") in ("payer-action", "approve")
        ),
        None,
    )
    if not order.get("id") or not approval_url:
        raise RuntimeError("PayPal did not return an order ID and buyer approval URL.")
    order["approval_url"] = approval_url
    return order
