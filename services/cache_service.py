from contextlib import contextmanager
from pathlib import Path
from google import genai
from google.genai import types

from services.llm_client import PRO_MODEL

_CACHE_TTL = "1200s"  # 20분 안전망


def upload_file(client: genai.Client, file_path: str) -> types.File:
    return client.files.upload(file=Path(file_path))


def create_cache(
    client: genai.Client,
    model: str,
    contents: list,
    display_name: str,
    ttl_seconds: int = 1200,
) -> str:
    """캐시 생성 후 cache name 반환."""
    cache = client.caches.create(
        model=model,
        config=types.CreateCachedContentConfig(
            contents=contents,
            display_name=display_name,
            ttl=f"{ttl_seconds}s",
        ),
    )
    return cache.name


def delete_cache(client: genai.Client, cache_name: str) -> None:
    try:
        client.caches.delete(name=cache_name)
    except Exception:
        pass


@contextmanager
def cached_markdown(client: genai.Client, parsed_markdown: str, label: str, model: str = PRO_MODEL):
    """parsed_markdown을 캐시로 등록 → yield cache_name → 자동 삭제."""
    cache_name = create_cache(
        client=client,
        model=model,
        contents=[types.Content(role="user", parts=[types.Part(text=parsed_markdown)])],
        display_name=label,
    )
    try:
        yield cache_name
    finally:
        delete_cache(client, cache_name)
