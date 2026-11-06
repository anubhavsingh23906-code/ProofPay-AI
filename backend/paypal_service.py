"""
PayPal Sandbox Checkout helpers.

This module talks to PayPal's REST APIs:
1. Create an order (USD 1.00 technical test amount)
2. Read the order (to verify status and that it belongs to a task)
3. Capture the order only after the buyer has approved it

Ordinary PayPal Checkout is not escrow. Funds move when capture succeeds.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import (
    FRONTEND_URL,
    PAYPAL_BASE_URL,
    PAYPAL_CLIENT_ID,
    PAYPAL_CLIENT_SECRET,
    PAYPAL_TEST_AMOUNT,
    PAYPAL_TEST_CURRENCY,
)

APPROVAL_RELS = ("approve", "payer-action")


def _http() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


class PayPalAPIError(Exception):
    """Raised when PayPal returns an error we can show to the client."""

    def __init__(self, message: str, status_code: int = 502, details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def get_paypal_access_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise PayPalAPIError(
            "PayPal Sandbox credentials are missing. Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET.",
            status_code=500,
        )

    response = _http().post(
        f"{PAYPAL_BASE_URL}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
        headers={
            "Accept": "application/json",
            "Accept-Language": "en_US",
        },
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    _raise_for_paypal(response, "PayPal authentication failed")
    return response.json()["access_token"]


def _auth_headers(idempotency_key: str | None = None) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {get_paypal_access_token()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if idempotency_key:
        headers["PayPal-Request-Id"] = idempotency_key
    return headers


def _raise_for_paypal(response: requests.Response, fallback: str) -> None:
    if response.ok:
        return

    payload: Any
    try:
        payload = response.json()
    except ValueError:
        payload = response.text

    message = fallback
    if isinstance(payload, dict):
        message = (
            payload.get("message")
            or payload.get("error_description")
            or payload.get("name")
            or fallback
        )
        details = payload.get("details")
        if details:
            message = f"{message}: {details}"

    raise PayPalAPIError(message, status_code=502, details=payload)


def extract_approval_url(order: dict) -> str | None:
    """
    PayPal Checkout orders usually include rel=approve.
    Some payment-source flows use rel=payer-action instead.
    """
    links = order.get("links") or []
    by_rel: dict[str, str] = {}
    for link in links:
        rel = link.get("rel")
        href = link.get("href")
        if rel and href:
            by_rel[rel] = href

    for rel in APPROVAL_RELS:
        if rel in by_rel:
            return by_rel[rel]
    return None


def create_paypal_order(task_id: str) -> dict:
    """
    Create a USD 1.00 Sandbox order for testing.
    This amount is NOT converted from the task's INR budget.
    """
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": task_id,
                "custom_id": task_id,
                "description": "ProofPay AI Sandbox technical test transaction (USD 1.00). Not the INR task budget.",
                "amount": {
                    "currency_code": PAYPAL_TEST_CURRENCY,
                    "value": PAYPAL_TEST_AMOUNT,
                },
            }
        ],
        "application_context": {
            "brand_name": "ProofPay AI",
            "landing_page": "LOGIN",
            "user_action": "PAY_NOW",
            "shipping_preference": "NO_SHIPPING",
            "return_url": f"{FRONTEND_URL}/payment/success?task_id={task_id}",
            "cancel_url": f"{FRONTEND_URL}/payment/cancel?task_id={task_id}",
        },
    }

    response = _http().post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders",
        headers=_auth_headers(idempotency_key=f"proofpay-order-{task_id}"),
        json=payload,
        timeout=30,
    )
    _raise_for_paypal(response, "PayPal order creation failed")
    order = response.json()

    approval_url = extract_approval_url(order)
    if not approval_url:
        rels = [link.get("rel") for link in order.get("links") or []]
        raise PayPalAPIError(
            "No approval link found in PayPal response "
            f"(looked for approve and payer-action; received rels: {rels}).",
            status_code=502,
            details={"order_id": order.get("id"), "status": order.get("status"), "rels": rels},
        )

    return {
        "order_id": order["id"],
        "status": order.get("status"),
        "currency": PAYPAL_TEST_CURRENCY,
        "test_amount": PAYPAL_TEST_AMOUNT,
        "approval_url": approval_url,
        "links": order.get("links", []),
    }


def get_paypal_order(order_id: str) -> dict:
    response = _http().get(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}",
        headers=_auth_headers(),
        timeout=30,
    )
    _raise_for_paypal(response, "Failed to retrieve PayPal order")
    return response.json()


def capture_paypal_order(order_id: str) -> dict:
    response = _http().post(
        f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
        headers=_auth_headers(idempotency_key=f"proofpay-capture-{order_id}"),
        timeout=30,
    )

    # Duplicate capture: treat as a request to re-read the order.
    if response.status_code == 422:
        payload = {}
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        issue = ""
        for detail in payload.get("details") or []:
            issue = (detail.get("issue") or "").upper()
            if issue in {"ORDER_ALREADY_CAPTURED", "CAPTURE_ALREADY_EXISTS"}:
                return get_paypal_order(order_id)
        _raise_for_paypal(response, "PayPal capture failed")

    _raise_for_paypal(response, "PayPal capture failed")
    return response.json()


def order_belongs_to_task(order: dict, task_id: str) -> bool:
    for unit in order.get("purchase_units") or []:
        if unit.get("custom_id") == task_id or unit.get("reference_id") == task_id:
            return True
    return False


def order_capture_id(order: dict) -> str | None:
    for unit in order.get("purchase_units") or []:
        payments = unit.get("payments") or {}
        for capture in payments.get("captures") or []:
            if capture.get("id"):
                return capture["id"]
    return None


def is_order_completed(order: dict) -> bool:
    if (order.get("status") or "").upper() == "COMPLETED":
        return True
    for unit in order.get("purchase_units") or []:
        payments = unit.get("payments") or {}
        for capture in payments.get("captures") or []:
            if (capture.get("status") or "").upper() == "COMPLETED":
                return True
    return False


if __name__ == "__main__":
    try:
        token = get_paypal_access_token()
        print("PayPal Sandbox authentication successful!")
        print("Access token received:", bool(token))
    except Exception as error:
        print("PayPal authentication failed.")
        print("Error:", str(error))
