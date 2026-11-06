import json
from unittest.mock import patch

from models import Task as TaskModel
from database import get_db


SAMPLE_TASK = {
    "title": "Design a product poster",
    "description": "Create a marketing poster for a student hackathon product launch event.",
    "budget": 5000,
    "currency": "INR",
    "deadline_days": 7,
}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_and_get_task(client):
    created = client.post("/tasks", json=SAMPLE_TASK)
    assert created.status_code == 200
    body = created.json()
    assert body["status"] == "draft"
    assert body["currency"] == "INR"
    assert body["budget"] == 5000

    task_id = body["task_id"]
    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == SAMPLE_TASK["title"]


def test_approve_agreement_requires_generation(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    response = client.post(
        f"/tasks/{task_id}/approve-agreement",
        json={"approved": True},
    )
    assert response.status_code == 400


def test_payment_requires_acceptance(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    response = client.post(f"/tasks/{task_id}/create-payment")
    assert response.status_code == 400


def _seed_accepted_task(client, task_id: str):
    db_gen = client.app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
        task.status = "client_accepted"
        task.agreement = {
            "deliverables": ["Poster PDF"],
            "acceptance_criteria": ["Includes product name"],
            "client_must_provide": [],
            "assumptions_or_questions": [],
            "revision_count": 0,
        }
        db.commit()
    finally:
        db.close()


def test_create_paypal_order_uses_approve_link(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    _seed_accepted_task(client, task_id)

    fake_order = {
        "order_id": "ORDER-1",
        "status": "CREATED",
        "currency": "USD",
        "test_amount": "1.00",
        "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-1",
        "links": [{"rel": "approve", "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-1"}],
    }

    with patch("main.create_paypal_order", return_value=fake_order):
        response = client.post(f"/tasks/{task_id}/create-payment")

    assert response.status_code == 200
    body = response.json()
    assert body["approval_url"].startswith("https://www.sandbox.paypal.com/")
    assert body["payment"]["test_amount"] == "1.00"
    assert body["payment"]["status"] == "created"


def test_capture_rejected_before_buyer_approval(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    _seed_accepted_task(client, task_id)

    fake_order = {
        "order_id": "ORDER-2",
        "status": "CREATED",
        "currency": "USD",
        "test_amount": "1.00",
        "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-2",
    }
    paypal_lookup = {
        "id": "ORDER-2",
        "status": "CREATED",
        "purchase_units": [{"custom_id": task_id, "reference_id": task_id}],
    }

    with patch("main.create_paypal_order", return_value=fake_order):
        assert client.post(f"/tasks/{task_id}/create-payment").status_code == 200

    with patch("main.get_paypal_order", return_value=paypal_lookup):
        response = client.post(
            f"/tasks/{task_id}/capture-payment",
            json={"order_id": "ORDER-2"},
        )

    assert response.status_code == 400
    assert "not approved" in response.json()["detail"].lower()


def test_capture_after_approval_marks_paid(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    _seed_accepted_task(client, task_id)

    fake_order = {
        "order_id": "ORDER-3",
        "status": "CREATED",
        "currency": "USD",
        "test_amount": "1.00",
        "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-3",
    }
    approved = {
        "id": "ORDER-3",
        "status": "APPROVED",
        "purchase_units": [{"custom_id": task_id, "reference_id": task_id}],
    }
    captured = {
        "id": "ORDER-3",
        "status": "COMPLETED",
        "purchase_units": [
            {
                "custom_id": task_id,
                "reference_id": task_id,
                "payments": {"captures": [{"id": "CAP-1", "status": "COMPLETED"}]},
            }
        ],
    }

    with patch("main.create_paypal_order", return_value=fake_order):
        assert client.post(f"/tasks/{task_id}/create-payment").status_code == 200

    with patch("main.get_paypal_order", return_value=approved), patch(
        "main.capture_paypal_order", return_value=captured
    ):
        response = client.post(
            f"/tasks/{task_id}/capture-payment",
            json={"order_id": "ORDER-3"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["task_status"] == "paid"
    assert body["payment"]["status"] == "completed"
    assert body["payment"]["capture_id"] == "CAP-1"


def test_capture_rejects_order_for_another_task(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    _seed_accepted_task(client, task_id)

    fake_order = {
        "order_id": "ORDER-4",
        "status": "CREATED",
        "currency": "USD",
        "test_amount": "1.00",
        "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-4",
    }
    foreign = {
        "id": "ORDER-4",
        "status": "APPROVED",
        "purchase_units": [{"custom_id": "someone-else", "reference_id": "someone-else"}],
    }

    with patch("main.create_paypal_order", return_value=fake_order):
        assert client.post(f"/tasks/{task_id}/create-payment").status_code == 200

    with patch("main.get_paypal_order", return_value=foreign):
        response = client.post(
            f"/tasks/{task_id}/capture-payment",
            json={"order_id": "ORDER-4"},
        )

    assert response.status_code == 400
    assert "does not belong" in response.json()["detail"].lower()


def test_duplicate_capture_is_idempotent(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    _seed_accepted_task(client, task_id)

    fake_order = {
        "order_id": "ORDER-5",
        "status": "CREATED",
        "currency": "USD",
        "test_amount": "1.00",
        "approval_url": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-5",
    }
    completed = {
        "id": "ORDER-5",
        "status": "COMPLETED",
        "purchase_units": [
            {
                "custom_id": task_id,
                "reference_id": task_id,
                "payments": {"captures": [{"id": "CAP-9", "status": "COMPLETED"}]},
            }
        ],
    }

    with patch("main.create_paypal_order", return_value=fake_order):
        assert client.post(f"/tasks/{task_id}/create-payment").status_code == 200

    with patch("main.get_paypal_order", return_value=completed):
        first = client.post(f"/tasks/{task_id}/capture-payment", json={})
        second = client.post(f"/tasks/{task_id}/capture-payment", json={})

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["payment"]["status"] == "completed"


def test_generate_agreement_saves_draft(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    fake_agreement = {
        "deliverables": ["A1 poster PDF"],
        "acceptance_criteria": ["Includes product name"],
        "client_must_provide": ["Logo file"],
        "assumptions_or_questions": ["Confirm colours"],
        "revision_count": 0,
    }

    with patch("main.ollama.generate", return_value={"response": json.dumps(fake_agreement)}):
        response = client.post(f"/tasks/{task_id}/generate-agreement")

    assert response.status_code == 200
    assert response.json()["status"] == "agreement_pending"
    assert response.json()["requires_client_approval"] is True

    approve = client.post(f"/tasks/{task_id}/approve-agreement", json={"approved": True})
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"


def test_submit_work_requires_approved_agreement(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    response = client.post(
        f"/tasks/{task_id}/submit-work",
        json={"submission_text": "I completed the poster work.", "file_names": []},
    )
    assert response.status_code == 400
