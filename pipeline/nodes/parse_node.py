import asyncio

import fitz
import pymupdf4llm
from google.genai import types

from config import OUTPUTS_DIR
from pipeline.state import AIAState
from prompts.parse_prompts import PARSE_IMAGE_PROMPT
from services.llm_client import LITE_MODEL, LLMClient, async_call_with_retry

_PARSE_CONCURRENCY = 150
_MIN_TEXT_CHARS = 50  # 이 미만이면 스캔/이미지 페이지로 판단


async def _parse_pages_vision(client, indexed_bytes: list[tuple[int, bytes]]) -> dict[int, str]:
    """(page_idx, img_bytes) 목록 → {page_idx: text} 반환"""
    sem = asyncio.Semaphore(_PARSE_CONCURRENCY)

    async def call_one(page_idx: int, img_bytes: bytes) -> tuple[int, str]:
        async with sem:
            response = await async_call_with_retry(
                client.aio.models.generate_content,
                model=LITE_MODEL,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                    PARSE_IMAGE_PROMPT,
                ],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="minimal"),
                ),
            )
            return page_idx, response.text

    results = await asyncio.gather(*[call_one(i, b) for i, b in indexed_bytes])
    return dict(results)


def parse_node(state: AIAState) -> dict:
    pdf_path = state["pdf_path"]
    run_id = state["run_id"]
    client = LLMClient.get_instance().client
    run_dir = OUTPUTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 체크포인트: parsed.md가 이미 있으면 스킵
    parsed_path = run_dir / "parsed.md"
    if parsed_path.exists():
        print("  [체크포인트] parsed.md 존재 → 스킵")
        parsed_markdown = parsed_path.read_text(encoding="utf-8")
        return {"parsed_markdown": parsed_markdown}

    # 1단계: 페이지별 텍스트 레이어 유무 판별
    doc = fitz.open(pdf_path)
    n_pages = len(doc)
    text_page_nums: list[int] = []
    image_page_nums: list[int] = []

    for i, page in enumerate(doc):
        has_text = len(page.get_text("text").strip()) >= _MIN_TEXT_CHARS
        (text_page_nums if has_text else image_page_nums).append(i)

    print(f"  총 {n_pages}페이지: 텍스트 {len(text_page_nums)}p / 이미지(스캔) {len(image_page_nums)}p")

    page_results: dict[int, str] = {}

    # 2단계: 텍스트 페이지 → pymupdf4llm (표·수식도 마크다운으로)
    if text_page_nums:
        chunks = pymupdf4llm.to_markdown(pdf_path, pages=text_page_nums, page_chunks=True)
        for chunk, page_idx in zip(chunks, text_page_nums):
            page_results[page_idx] = chunk["text"]
        print(f"  pymupdf4llm 완료: {len(text_page_nums)}페이지")

    # 3단계: 이미지/스캔 페이지 → Gemini Lite vision
    if image_page_nums:
        indexed_bytes = [
            (i, doc[i].get_pixmap(dpi=150).tobytes("png"))
            for i in image_page_nums
        ]
        vision_results = asyncio.get_event_loop().run_until_complete(_parse_pages_vision(client, indexed_bytes))
        page_results.update(vision_results)
        print(f"  Gemini vision 완료: {len(image_page_nums)}페이지")

    doc.close()

    # 4단계: 페이지 순서대로 합치기
    page_sections = [
        f"[페이지 {i + 1}]\n{page_results.get(i, '')}"
        for i in range(n_pages)
    ]
    parsed_markdown = "\n\n---\n\n".join(page_sections)

    (run_dir / "parsed.md").write_text(parsed_markdown, encoding="utf-8")
    return {"parsed_markdown": parsed_markdown}
