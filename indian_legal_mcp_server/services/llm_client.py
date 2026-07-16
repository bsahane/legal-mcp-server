from typing import Optional
from indian_legal_mcp_server.config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model = settings.LLM_MODEL
        self.fallback = settings.LLM_FALLBACK_PROVIDER

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ) -> str:
        if self.provider == "anthropic":
            return await self._call_anthropic(
                system_prompt, user_prompt, max_tokens, temperature
            )
        elif self.provider == "openai":
            return await self._call_openai(
                system_prompt, user_prompt, max_tokens, temperature
            )
        else:
            return self._mock_response(system_prompt, user_prompt)

    async def classify(self, text: str, categories: list) -> dict:
        system = (
            "Classify the following legal scenario into one of these categories: "
            + ", ".join(categories)
        )
        prompt = f'Scenario: {text}\n\nRespond with only the category name and confidence (0-1) as JSON: {{"category": "...", "confidence": 0.0}}'
        result = await self.generate(system, prompt, max_tokens=200)
        import json

        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "category": categories[0] if categories else "unknown",
                "confidence": 0.5,
            }

    async def _call_anthropic(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.content[0].text

    async def _call_openai(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        return "Mock LLM response. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env for real responses."


_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
