"""
Provider-neutral structured generation for ProofPay AI.

Business endpoints choose the schema and prompt. This module chooses Ollama
or Gemini from AI_PROVIDER and returns a validated Pydantic object.
A provider failure never falls back to the other provider.
"""

import json
import re

import requests
from pydantic import BaseModel, ValidationError

import ollama
from config import (
    AI_PROVIDER,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    OLLAMA_HOST,
    OLLAMA_MODEL,
)

AI_TIMEOUT_SECONDS = 120


class AIServiceError(Exception):
    """The model did not produce a usable structured result."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


def provider_health() -> dict:
    """Report the selected provider without revealing credentials."""
    provider = _provider_name()

    if provider == "gemini":
        return {
            "ai_provider": "gemini",
            "ai_model": GEMINI_MODEL,
            "ai": "configured" if GEMINI_API_KEY else "missing_api_key",
            "ollama": "not_selected",
        }

    if provider != "ollama":
        return {
            "ai_provider": provider or "unset",
            "ai_model": None,
            "ai": "unsupported_provider",
            "ollama": "not_selected",
        }

    ollama_status = "unavailable"
    try:
        ping = requests.get(
            f"{OLLAMA_HOST.rstrip('/')}/api/tags",
            timeout=2,
        )
        if ping.ok:
            ollama_status = "available"
    except requests.RequestException:
        ollama_status = "unavailable"

    return {
        "ai_provider": "ollama",
        "ai_model": OLLAMA_MODEL,
        "ai": ollama_status,
        "ollama": ollama_status,
    }


def generate_structured(
    prompt: str,
    schema_model: type[BaseModel],
    *,
    system: str | None = None,
    operation: str,
) -> BaseModel:
    """
    Call the configured provider and validate the JSON against schema_model.

    operation is "agreement" or "verification" and is only used in safe errors.
    """
    provider = _provider_name()
    schema = schema_model.model_json_schema()

    if provider == "gemini":
        raw = _gemini_text(prompt, schema, system, operation)
    elif provider == "ollama":
        raw = _ollama_text(prompt, schema, system, operation)
    else:
        raise _failure(
            operation,
            "AI_PROVIDER must be either ollama or gemini. No automatic fallback was used.",
        )

    return _parse_model(raw, schema_model, operation)


def _provider_name() -> str:
    return (AI_PROVIDER or "").strip().lower()


def _failure(operation: str, reason: str) -> AIServiceError:
    if operation == "agreement":
        detail = f"AI agreement generation is unavailable. {reason} Nothing was saved."
    else:
        detail = (
            "AI verification is unavailable. "
            f"{reason} The submission was not marked verified."
        )
    return AIServiceError(detail)


def _parse_model(raw: str, schema_model: type[BaseModel], operation: str) -> BaseModel:
    text = (raw or "").strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    if not text:
        raise _failure(operation, "The model response was empty.")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        raise _failure(
            operation,
            "The model response was not valid structured JSON.",
        ) from None

    try:
        return schema_model.model_validate(parsed)
    except ValidationError:
        raise _failure(
            operation,
            "The model response did not match the required format.",
        ) from None


def _ollama_text(
    prompt: str,
    schema: dict,
    system: str | None,
    operation: str,
) -> str:
    client = ollama.Client(host=OLLAMA_HOST, timeout=AI_TIMEOUT_SECONDS)
    try:
        try:
            if system:
                response = client.chat(
                    model=OLLAMA_MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    format=schema,
                )
            else:
                response = client.generate(
                    model=OLLAMA_MODEL,
                    prompt=prompt,
                    format=schema,
                    options={"temperature": 0, "num_ctx": 2048},
                    stream=False,
                )
        except Exception:
            raise _failure(
                operation,
                "Start Ollama with the configured model, then try again.",
            ) from None

        try:
            if system:
                message = response["message"] if isinstance(response, dict) else response.message
                content = message["content"] if isinstance(message, dict) else message.content
            else:
                content = response["response"] if isinstance(response, dict) else response.response
        except Exception:
            raise _failure(
                operation,
                "The model response was not valid structured JSON.",
            ) from None
    finally:
        client.close()

    return content or ""


def _gemini_text(
    prompt: str,
    schema: dict,
    system: str | None,
    operation: str,
) -> str:
    if not GEMINI_API_KEY:
        raise _failure(
            operation,
            "GEMINI_API_KEY is not set for AI_PROVIDER=gemini.",
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        raise _failure(
            operation,
            "The google-genai package is not installed.",
        ) from None

    config = types.GenerateContentConfig(
        temperature=0,
        max_output_tokens=2048,
        response_mime_type="application/json",
        response_json_schema=schema,
        system_instruction=system,
    )

    try:
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=AI_TIMEOUT_SECONDS * 1000),
        )
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
            text = response.text
        finally:
            client.close()
    except AIServiceError:
        raise
    except Exception:
        raise _failure(
            operation,
            "The Gemini request failed. Try again later.",
        ) from None

    return text or ""
