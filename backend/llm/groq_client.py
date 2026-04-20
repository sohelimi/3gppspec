"""Groq LLM client — free tier, Llama 3.3 70B."""

from groq import Groq, AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential

MODEL_NAME = "llama-3.3-70b-versatile"

_client: Groq | None = None
_async_client: AsyncGroq | None = None


def get_client() -> Groq:
    global _client
    if _client is None:
        from backend.config import settings
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def get_async_client() -> AsyncGroq:
    global _async_client
    if _async_client is None:
        from backend.config import settings
        _async_client = AsyncGroq(api_key=settings.groq_api_key)
    return _async_client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate(prompt: str, system_prompt: str = None, temperature: float = 0.2) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    response = get_client().chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=2048,
    )
    return response.choices[0].message.content


async def generate_stream(prompt: str, system_prompt: str = None, temperature: float = 0.2):
    """Async generator yielding streamed text chunks."""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    stream = await get_async_client().chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
        max_tokens=2048,
        stream=True,
    )
    async for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            yield token
