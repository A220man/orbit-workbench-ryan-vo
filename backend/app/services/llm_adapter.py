"""Pluggable server-side LLM adapter.

Supports OpenAI-compatible, Anthropic messages, Gemini generateContent, and Ollama.
Deterministic offline fallback when no LLM_API_KEY is configured.
Strictly server-side credential isolation and redacted error logging.
"""
import re
from typing import Dict, List, Optional
import httpx
from app.core.config import settings
from app.models.schemas import DiagramContent, LLMExplainResponse


class LLMAdapter:
    """Configurable client for LLM advisory diagram explanations."""

    PROVIDER_DEFAULTS = {
        "openai-compatible": {
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
        },
        "anthropic": {
            "base_url": "https://api.anthropic.com/v1",
            "model": "claude-3-5-sonnet-20241022",
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "model": "gemini-1.5-flash",
        },
        "ollama": {
            "base_url": "http://127.0.0.1:11434/api",
            "model": "llama3.2:latest",
        },
    }

    @classmethod
    def redact_credentials(cls, text: str) -> str:
        """Removes potential secrets or key substrings from error messages."""
        if not text:
            return ""
        # Redact any bearer or key tokens
        text = re.sub(r"Bearer\s+[A-Za-z0-9_\-\.]{10,}", "Bearer [REDACTED]", text)
        text = re.sub(r"(?:sk-[A-Za-z0-9_\-]{15,}|key-[A-Za-z0-9_\-]{15,})", "[REDACTED_KEY]", text)
        return text

    @classmethod
    async def explain_diagram(
        cls,
        spec: DiagramContent,
        question: Optional[str] = None,
    ) -> LLMExplainResponse:
        """Generates an advisory explanation grounded in the actual diagram records."""
        # Extract grounded entities from spec
        grounded_entities: List[str] = []
        if spec.title:
            grounded_entities.append(f"Title: {spec.title}")
        if spec.eyebrow:
            grounded_entities.append(f"Category: {spec.eyebrow}")

        data = spec.data or {}
        if "subscription" in data:
            grounded_entities.append(f"Subscription: {data['subscription']}")
        if "vnet" in data:
            grounded_entities.append(f"VNet: {data['vnet']}")
        for snet in data.get("subnets", []):
            grounded_entities.append(f"Subnet: {snet.get('name', 'snet')}")
            for n in snet.get("nodes", []):
                grounded_entities.append(f"Node: {n.get('label')} ({n.get('ip')})")
        for paas in data.get("paas_services", []):
            grounded_entities.append(f"PaaS: {paas.get('label')} -> {paas.get('target_pe')}")
        for item in data.get("items", []):
            grounded_entities.append(f"Data Item: {item.get('label')} = {item.get('value', item.get('b'))}")

        # Offline deterministic explanation when LLM_API_KEY is not configured
        if not settings.llm_api_key and settings.llm_provider != "ollama":
            offline_text = (
                f"Deterministic Offline Analysis of '{spec.title}':\n"
                f"- Architecture / Data Category: {spec.eyebrow or 'General Specification'}\n"
                f"- Total Identified Entities: {len(grounded_entities)}\n"
                f"- Primary Components: {', '.join(grounded_entities[:6]) if grounded_entities else 'None'}\n"
                f"- Advisory Note: LLM explanations are opt-in. Configure LLM_API_KEY to query an external reasoning provider."
            )
            return LLMExplainResponse(
                provider="offline-deterministic",
                model="local-rule-engine",
                explanation=offline_text,
                grounded_entities=grounded_entities,
                is_advisory=True,
            )

        # Provider execution
        provider = settings.llm_provider.lower()
        model = settings.llm_model or cls.PROVIDER_DEFAULTS.get(provider, {}).get("model", "default")
        base_url = settings.llm_base_url or cls.PROVIDER_DEFAULTS.get(provider, {}).get("base_url", "")

        prompt_text = (
            f"You are an editorial diagram reviewer. Explain this diagram specification clearly and accurately.\n"
            f"Title: {spec.title}\n"
            f"Entities: {', '.join(grounded_entities)}\n"
            f"Question: {question or 'Summarize the architecture topology and key dataflows.'}"
        )

        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                if provider == "anthropic":
                    headers = {
                        "x-api-key": settings.llm_api_key or "",
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    }
                    body = {
                        "model": model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt_text}],
                    }
                    resp = await client.post(f"{base_url.rstrip('/')}/messages", json=body, headers=headers)
                    resp.raise_for_status()
                    result_json = resp.json()
                    content_blocks = result_json.get("content", [])
                    explanation = "".join(b.get("text", "") for b in content_blocks)

                elif provider == "gemini":
                    headers = {"content-type": "application/json"}
                    url = f"{base_url.rstrip('/')}/models/{model}:generateContent?key={settings.llm_api_key}"
                    body = {"contents": [{"parts": [{"text": prompt_text}]}]}
                    resp = await client.post(url, json=body, headers=headers)
                    resp.raise_for_status()
                    result_json = resp.json()
                    candidates = result_json.get("candidates", [])
                    explanation = candidates[0]["content"]["parts"][0]["text"] if candidates else "No output generated."

                elif provider == "ollama":
                    body = {"model": model, "prompt": prompt_text, "stream": False}
                    resp = await client.post(f"{base_url.rstrip('/')}/generate", json=body)
                    resp.raise_for_status()
                    result_json = resp.json()
                    explanation = result_json.get("response", "No response from Ollama.")

                else:
                    # Default: OpenAI-compatible
                    headers = {
                        "Authorization": f"Bearer {settings.llm_api_key or ''}",
                        "Content-Type": "application/json",
                    }
                    body = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are an expert editorial systems architect."},
                            {"role": "user", "content": prompt_text},
                        ],
                        "temperature": 0.2,
                    }
                    resp = await client.post(f"{base_url.rstrip('/')}/chat/completions", json=body, headers=headers)
                    resp.raise_for_status()
                    result_json = resp.json()
                    explanation = result_json["choices"][0]["message"]["content"]

                return LLMExplainResponse(
                    provider=provider,
                    model=model,
                    explanation=explanation,
                    grounded_entities=grounded_entities,
                    is_advisory=True,
                )

        except Exception as e:
            redacted_err = cls.redact_credentials(str(e))
            return LLMExplainResponse(
                provider=provider,
                model=model,
                explanation=f"Provider Error ({provider}): Unable to retrieve advisory explanation. Details: {redacted_err}",
                grounded_entities=grounded_entities,
                is_advisory=True,
            )
