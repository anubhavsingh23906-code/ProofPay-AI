from paypal_service import extract_approval_url, order_belongs_to_task


def test_extracts_approve_link():
    order = {
        "links": [
            {"rel": "self", "href": "https://api-m.sandbox.paypal.com/v2/checkout/orders/1"},
            {"rel": "approve", "href": "https://www.sandbox.paypal.com/checkoutnow?token=1"},
        ]
    }
    assert extract_approval_url(order).endswith("token=1")


def test_extracts_payer_action_link():
    order = {
        "links": [
            {"rel": "payer-action", "href": "https://www.sandbox.paypal.com/checkoutnow?token=2"},
        ]
    }
    assert "token=2" in extract_approval_url(order)


def test_prefers_approve_over_payer_action():
    order = {
        "links": [
            {"rel": "payer-action", "href": "https://example.com/payer"},
            {"rel": "approve", "href": "https://example.com/approve"},
        ]
    }
    assert extract_approval_url(order) == "https://example.com/approve"


def test_order_task_match():
    order = {"purchase_units": [{"custom_id": "abc", "reference_id": "abc"}]}
    assert order_belongs_to_task(order, "abc")
    assert not order_belongs_to_task(order, "zzz")
