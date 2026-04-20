"""Gemini 1.5 Flash client using the new google-genai SDK."""

from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

MODEL_NAME = "gemini-2.0-flash-lite"

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        from backend.config import settings
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate(prompt: str, system_prompt: str = None, temperature: float = 0.2) -> str:
    client = get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_prompt,
    )
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    )
    return response.text


async def generate_stream(prompt: str, system_prompt: str = None, temperature: float = 0.2):
    """Async generator yielding streamed text chunks."""
    client = get_client()
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system_prompt,
    )
    async for chunk in await client.aio.models.generate_content_stream(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    ):
        if chunk.text:
            yield chunk.text
