import json
from unittest.mock import patch

from ai_service import AIServiceError
from schemas import Agreement, VerificationResult
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

    with patch("main.generate_structured", return_value=Agreement.model_validate(fake_agreement)):
        response = client.post(f"/tasks/{task_id}/generate-agreement")

    assert response.status_code == 200
    assert response.json()["status"] == "agreement_pending"
    assert response.json()["requires_client_approval"] is True

    approve = client.post(f"/tasks/{task_id}/approve-agreement", json={"approved": True})
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"


def test_generate_agreement_does_not_save_malformed_ai_output(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]

    with patch(
        "main.generate_structured",
        side_effect=AIServiceError(
            "AI agreement generation is unavailable. "
            "The model response was not valid structured JSON. Nothing was saved."
        ),
    ):
        response = client.post(f"/tasks/{task_id}/generate-agreement")

    assert response.status_code == 502
    assert "Nothing was saved" in response.json()["detail"]
    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.json()["status"] == "draft"
    assert fetched.json()["agreement"] is None


def test_verify_work_saves_advisory_result(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    agreement = {
        "deliverables": ["Poster PDF"],
        "acceptance_criteria": ["Includes product name"],
        "client_must_provide": [],
        "assumptions_or_questions": [],
        "revision_count": 0,
    }
    with patch("main.generate_structured", return_value=Agreement.model_validate(agreement)):
        assert client.post(f"/tasks/{task_id}/generate-agreement").status_code == 200
    assert client.post(
        f"/tasks/{task_id}/approve-agreement",
        json={"approved": True},
    ).status_code == 200

    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
    uploaded = client.post(
        f"/tasks/{task_id}/upload-files",
        files=[("files", ("poster.pdf", pdf, "application/pdf"))],
    )
    assert uploaded.status_code == 200

    submitted = client.post(
        f"/tasks/{task_id}/submit-work",
        json={"submission_text": "Poster PDF is attached.", "file_names": ["poster.pdf"]},
    )
    assert submitted.status_code == 200

    verification = VerificationResult(
        completed_requirements=["Poster PDF"],
        missing_requirements=[],
        unclear_requirements=["Includes product name"],
        feedback="Text evidence is incomplete.",
        recommendation="manual_review",
    )
    with patch("main.extract_pdf_text", return_value="Poster PDF for the launch"), patch(
        "main.generate_structured",
        return_value=verification,
    ):
        response = client.post(f"/tasks/{task_id}/verify-work")

    assert response.status_code == 200
    body = response.json()
    assert body["client_must_make_final_decision"] is True
    assert body["verification"]["recommendation"] == "manual_review"
    assert body["status"] == "verification_completed"
    assert "payment" not in body


def test_verify_work_failure_does_not_mark_verified(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    agreement = {
        "deliverables": ["Poster PDF"],
        "acceptance_criteria": ["Includes product name"],
        "client_must_provide": [],
        "assumptions_or_questions": [],
        "revision_count": 0,
    }
    with patch("main.generate_structured", return_value=Agreement.model_validate(agreement)):
        assert client.post(f"/tasks/{task_id}/generate-agreement").status_code == 200
    client.post(f"/tasks/{task_id}/approve-agreement", json={"approved": True})
    pdf = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"
    assert client.post(
        f"/tasks/{task_id}/upload-files",
        files=[("files", ("poster.pdf", pdf, "application/pdf"))],
    ).status_code == 200
    client.post(
        f"/tasks/{task_id}/submit-work",
        json={"submission_text": "Poster PDF is attached.", "file_names": ["poster.pdf"]},
    )

    with patch("main.extract_pdf_text", return_value="Poster PDF"), patch(
        "main.generate_structured",
        side_effect=AIServiceError(
            "AI verification is unavailable. The Gemini request failed. "
            "Try again later. The submission was not marked verified."
        ),
    ):
        response = client.post(f"/tasks/{task_id}/verify-work")

    assert response.status_code == 502
    assert "not marked verified" in response.json()["detail"]
    fetched = client.get(f"/tasks/{task_id}")
    assert fetched.json()["status"] == "submitted"
    assert fetched.json()["verification"] is None


def test_health_reports_selected_gemini_provider(client, monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "")
    monkeypatch.setattr("ai_service.GEMINI_MODEL", "gemini-2.5-flash")
    with patch("ai_service.requests.get") as get:
        response = client.get("/health")
    assert response.status_code == 200
    get.assert_not_called()
    body = response.json()
    assert body["status"] == "healthy"
    assert body["ai_provider"] == "gemini"
    assert body["ai_model"] == "gemini-2.5-flash"
    assert body["ai"] == "missing_api_key"
    assert body["ollama"] == "not_selected"


def test_submit_work_requires_approved_agreement(client):
    task_id = client.post("/tasks", json=SAMPLE_TASK).json()["task_id"]
    response = client.post(
        f"/tasks/{task_id}/submit-work",
        json={"submission_text": "I completed the poster work.", "file_names": []},
    )
    assert response.status_code == 400
