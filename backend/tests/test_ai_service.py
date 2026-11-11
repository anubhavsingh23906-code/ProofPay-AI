import json
from unittest.mock import MagicMock, patch

import pytest

from ai_service import AIServiceError, generate_structured
from schemas import Agreement, VerificationResult


AGREEMENT = {
    "deliverables": ["A1 poster PDF"],
    "acceptance_criteria": ["Includes product name"],
    "client_must_provide": ["Logo file"],
    "assumptions_or_questions": ["Confirm colours"],
    "revision_count": 0,
}

VERIFICATION = {
    "completed_requirements": ["A1 poster PDF"],
    "missing_requirements": [],
    "unclear_requirements": ["Includes product name"],
    "feedback": "The product name is not in the extracted text.",
    "recommendation": "manual_review",
}


def test_ollama_provider_uses_generate_for_agreements(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "ollama")
    monkeypatch.setattr("ai_service.OLLAMA_HOST", "http://localhost:11434")
    monkeypatch.setattr("ai_service.OLLAMA_MODEL", "qwen3:1.7b")

    fake = MagicMock()
    fake.generate.return_value = {"response": json.dumps(AGREEMENT)}

    with patch("ai_service.ollama.Client", return_value=fake) as constructor:
        result = generate_structured("Draft an agreement", Agreement, operation="agreement")

    constructor.assert_called_once_with(host="http://localhost:11434", timeout=120)
    assert fake.generate.call_args.kwargs["model"] == "qwen3:1.7b"
    fake.chat.assert_not_called()
    assert result.deliverables == ["A1 poster PDF"]
    assert result.revision_count == 0


def test_ollama_provider_uses_chat_for_verification(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "ollama")
    fake = MagicMock()
    fake.chat.return_value = {"message": {"content": json.dumps(VERIFICATION)}}

    with patch("ai_service.ollama.Client", return_value=fake):
        result = generate_structured(
            "Compare the work",
            VerificationResult,
            system="Return JSON only",
            operation="verification",
        )

    fake.chat.assert_called_once()
    fake.generate.assert_not_called()
    assert result.recommendation == "manual_review"


def test_gemini_provider_uses_google_genai_and_not_ollama(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr("ai_service.GEMINI_MODEL", "gemini-3.5-flash-lite")

    response = MagicMock()
    response.text = json.dumps(AGREEMENT)
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = response

    with patch("google.genai.Client", return_value=fake_client) as constructor, patch(
        "ai_service.ollama.Client"
    ) as ollama_client:
        result = generate_structured("Draft an agreement", Agreement, operation="agreement")

    ollama_client.assert_not_called()
    assert constructor.call_args.kwargs["api_key"] == "test-key-not-real"
    call = fake_client.models.generate_content.call_args.kwargs
    assert call["model"] == "gemini-3.5-flash-lite"
    fake_client.close.assert_called_once_with()
    assert call["config"].response_mime_type == "application/json"
    assert result.acceptance_criteria == ["Includes product name"]


def test_missing_gemini_key_does_not_call_ollama(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "")

    with patch("ai_service.ollama.Client") as ollama_client, patch(
        "google.genai.Client"
    ) as gemini_client:
        with pytest.raises(AIServiceError) as caught:
            generate_structured("Draft an agreement", Agreement, operation="agreement")

    assert "GEMINI_API_KEY" in caught.value.detail
    assert "Nothing was saved" in caught.value.detail
    ollama_client.assert_not_called()
    gemini_client.assert_not_called()


def test_gemini_api_error_hides_exception_text(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "test-key-not-real")

    fake_client = MagicMock()
    fake_client.models.generate_content.side_effect = TimeoutError(
        "timed out while using test-key-not-real"
    )

    with patch("google.genai.Client", return_value=fake_client):
        with pytest.raises(AIServiceError) as caught:
            generate_structured(
                "Compare the work",
                VerificationResult,
                system="Return JSON only",
                operation="verification",
            )

    assert "Gemini request failed" in caught.value.detail
    assert "not marked verified" in caught.value.detail
    assert "test-key-not-real" not in caught.value.detail
    fake_client.close.assert_called_once_with()


def test_gemini_malformed_json_is_rejected(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "test-key-not-real")

    response = MagicMock()
    response.text = "this is not json"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = response

    with patch("google.genai.Client", return_value=fake_client):
        with pytest.raises(AIServiceError) as caught:
            generate_structured("Draft an agreement", Agreement, operation="agreement")

    assert "not valid structured JSON" in caught.value.detail


def test_gemini_accepts_fenced_json(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "test-key-not-real")

    response = MagicMock()
    response.text = "```json\n" + json.dumps(VERIFICATION) + "\n```"
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = response

    with patch("google.genai.Client", return_value=fake_client):
        result = generate_structured(
            "Compare the work",
            VerificationResult,
            operation="verification",
        )

    assert result.unclear_requirements == ["Includes product name"]


def test_gemini_schema_mismatch_is_rejected(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "gemini")
    monkeypatch.setattr("ai_service.GEMINI_API_KEY", "test-key-not-real")

    response = MagicMock()
    response.text = json.dumps({"deliverables": "not-a-list"})
    fake_client = MagicMock()
    fake_client.models.generate_content.return_value = response

    with patch("google.genai.Client", return_value=fake_client):
        with pytest.raises(AIServiceError) as caught:
            generate_structured("Draft an agreement", Agreement, operation="agreement")

    assert "did not match the required format" in caught.value.detail


def test_unsupported_provider_does_not_fall_back(monkeypatch):
    monkeypatch.setattr("ai_service.AI_PROVIDER", "openai")

    with patch("ai_service.ollama.Client") as ollama_client, patch(
        "google.genai.Client"
    ) as gemini_client:
        with pytest.raises(AIServiceError) as caught:
            generate_structured("Draft an agreement", Agreement, operation="agreement")

    assert "No automatic fallback" in caught.value.detail
    ollama_client.assert_not_called()
    gemini_client.assert_not_called()
