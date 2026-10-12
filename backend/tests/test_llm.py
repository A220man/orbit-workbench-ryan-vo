"""Unit tests for the LLM adapter with mocked network calls."""
import pytest
import httpx
from app.models.schemas import DiagramContent
from app.services.llm_adapter import LLMAdapter
from app.core.config import settings


@pytest.mark.asyncio
async def test_offline_deterministic_explanation():
    # When no key is set, returns deterministic local rule-based analysis
    orig_key = settings.llm_api_key
    try:
        settings.llm_api_key = None
        content = DiagramContent(
            eyebrow="CLOUD ARCHITECTURE",
            title="Production Hub Topology",
            data={"subscription": "Sub-01", "vnet": "10.0.0.0/16"},
        )
        res = await LLMAdapter.explain_diagram(content)
        assert res.provider == "offline-deterministic"
        assert res.is_advisory
        assert "Deterministic Offline Analysis" in res.explanation
        assert any("Production Hub Topology" in e for e in res.grounded_entities)
    finally:
        settings.llm_api_key = orig_key


@pytest.mark.asyncio
async def test_mocked_openai_provider(monkeypatch):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {"message": {"content": "This architecture implements clean private endpoint separation."}}
                ]
            }

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    orig_key = settings.llm_api_key
    orig_provider = settings.llm_provider
    try:
        settings.llm_api_key = "synthetic-test-key"
        settings.llm_provider = "openai-compatible"
        content = DiagramContent(title="Mocked Architecture")
        res = await LLMAdapter.explain_diagram(content)
        assert res.provider == "openai-compatible"
        assert "clean private endpoint separation" in res.explanation
    finally:
        settings.llm_api_key = orig_key
        settings.llm_provider = orig_provider
