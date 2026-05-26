import contextvars
import json
import os
import threading
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
import httpx

load_dotenv()

PRO_MODEL = "models/gemini-3.1-pro-preview"
FLASH_MODEL = "models/gemini-3.5-flash"
LITE_MODEL = "models/gemini-3.1-flash-lite"

# ── 비용 추적 ─────────────────────────────────────────────────────────────────

_run_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("run_id", default=None)
_usage_lock = threading.Lock()
_usage_store: dict[str, list[dict]] = {}

# context var가 전파되지 않는 edge case를 위한 thread-id → run_id 폴백 맵
_thread_run_ids: dict[int, str] = {}

# 모델별 단가 (USD / 1M tokens) — Gemini 3 유료 등급 기준
_PRICING: dict[str, dict] = {
    PRO_MODEL:   {"input": 1.25, "output": 10.0, "cached": 0.31},
    FLASH_MODEL: {"input": 0.50, "output": 3.00,  "cached": 0.05},
    LITE_MODEL:  {"input": 0.10, "output": 0.40,  "cached": 0.025},
}
_DEFAULT_PRICING = {"input": 0.50, "output": 3.00, "cached": 0.05}


def begin_run_tracking(run_id: str) -> None:
    _run_id_ctx.set(run_id)
    tid = threading.get_ident()
    with _usage_lock:
        if run_id not in _usage_store:
            _usage_store[run_id] = []
        _thread_run_ids[tid] = run_id


def end_run_thread_tracking() -> None:
    """파이프라인 스레드 종료 시 thread-id 맵에서 제거."""
    tid = threading.get_ident()
    with _usage_lock:
        _thread_run_ids.pop(tid, None)


def _get_run_id() -> str | None:
    """context var 우선, 없으면 thread-id 폴백으로 run_id 조회."""
    run_id = _run_id_ctx.get()
    if run_id:
        return run_id
    tid = threading.get_ident()
    with _usage_lock:
        return _thread_run_ids.get(tid)


def _record_usage(response, model: str) -> None:
    run_id = _get_run_id()
    if not run_id:
        print(f"  [usage:WARN] run_id not found (thread={threading.get_ident()})")
        return
    meta = getattr(response, "usage_metadata", None)
    if meta is None:
        print(f"  [usage:WARN] no usage_metadata (model={model})")
        return

    input_tokens   = getattr(meta, "prompt_token_count",         0) or 0
    output_tokens  = getattr(meta, "candidates_token_count",     0) or 0
    cached_tokens  = getattr(meta, "cached_content_token_count", 0) or 0
    thinking_tokens = getattr(meta, "thoughts_token_count",      0) or 0
    total_tokens   = getattr(meta, "total_token_count",          0) or 0

    # thoughts_token_count는 output에 합산 (별도 청구)
    billable_output = output_tokens + thinking_tokens

    # 주요 필드가 모두 0인데 total만 있는 경우 (SDK 버전 차이 방어)
    if input_tokens == 0 and billable_output == 0 and total_tokens > 0:
        input_tokens   = total_tokens // 2
        billable_output = total_tokens - input_tokens

    with _usage_lock:
        if run_id not in _usage_store:
            return
        _usage_store[run_id].append({
            "model":           model,
            "input_tokens":    input_tokens,
            "output_tokens":   billable_output,
            "cached_tokens":   cached_tokens,
            "thinking_tokens": thinking_tokens,
        })


def record_embed_usage(token_count: int, model: str = "embedding") -> None:
    """embed_content 호출의 토큰 수를 수동으로 기록 (usage_metadata가 없는 경우)."""
    run_id = _get_run_id()
    if not run_id:
        return
    with _usage_lock:
        if run_id not in _usage_store:
            return
        _usage_store[run_id].append({
            "model":           model,
            "input_tokens":    token_count,
            "output_tokens":   0,
            "cached_tokens":   0,
            "thinking_tokens": 0,
        })


def get_usage_report(run_id: str) -> dict:
    with _usage_lock:
        calls = list(_usage_store.get(run_id, []))

    by_model: dict[str, dict] = {}
    total_cost = 0.0

    for c in calls:
        m = c["model"]
        if m not in by_model:
            by_model[m] = {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                           "cached_tokens": 0, "thinking_tokens": 0, "cost_usd": 0.0}
        p = _PRICING.get(m, _DEFAULT_PRICING)
        inp, out, cac = c["input_tokens"], c["output_tokens"], c["cached_tokens"]
        thi = c.get("thinking_tokens", 0)
        cost = (max(0, inp - cac) * p["input"] + cac * p["cached"] + out * p["output"]) / 1_000_000
        by_model[m]["calls"]           += 1
        by_model[m]["input_tokens"]    += inp
        by_model[m]["output_tokens"]   += out
        by_model[m]["cached_tokens"]   += cac
        by_model[m]["thinking_tokens"] += thi
        by_model[m]["cost_usd"]        = round(by_model[m]["cost_usd"] + cost, 6)
        total_cost += cost

    return {
        "calls": len(calls),
        "total_input_tokens":    sum(c["input_tokens"]    for c in calls),
        "total_output_tokens":   sum(c["output_tokens"]   for c in calls),
        "total_cached_tokens":   sum(c["cached_tokens"]   for c in calls),
        "total_thinking_tokens": sum(c.get("thinking_tokens", 0) for c in calls),
        "estimated_cost_usd":    round(total_cost, 6),
        "by_model": by_model,
    }


def save_usage(run_id: str, run_dir: Path) -> dict:
    report = get_usage_report(run_id)
    (run_dir / "usage.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    end_run_thread_tracking()
    with _usage_lock:
        _usage_store.pop(run_id, None)
    return report


# ── LLM 호출 ─────────────────────────────────────────────────────────────────

def call_with_retry(fn, *args, max_retries: int = 5, base_delay: float = 10.0, **kwargs):
    """503/429 및 소켓 오류 발생 시 지수 백오프로 재시도. usage_metadata 자동 수집."""
    for attempt in range(max_retries):
        try:
            response = fn(*args, **kwargs)
            _record_usage(response, kwargs.get("model", "unknown"))
            return response
        except (genai_errors.ServerError, genai_errors.ClientError) as e:
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            if code not in (429, 503) or attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"  [{code}] 재시도 {attempt + 1}/{max_retries} ({delay:.0f}s 대기)")
            time.sleep(delay)
        except httpx.TransportError as e:
            # WinError 10038 등 소켓 수준 일시 오류 — 짧은 딜레이 후 재시도
            if attempt == max_retries - 1:
                raise
            delay = 2.0 * (2 ** attempt)
            print(f"  [네트워크 오류] {type(e).__name__}: {e} — 재시도 {attempt + 1}/{max_retries} ({delay:.0f}s 대기)")
            time.sleep(delay)


async def async_call_with_retry(coro_fn, *args, max_retries: int = 5, base_delay: float = 10.0, **kwargs):
    """비동기 503/429 및 소켓 오류 발생 시 지수 백오프로 재시도. usage_metadata 자동 수집."""
    import asyncio
    for attempt in range(max_retries):
        try:
            response = await coro_fn(*args, **kwargs)
            _record_usage(response, kwargs.get("model", "unknown"))
            return response
        except (genai_errors.ServerError, genai_errors.ClientError) as e:
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            if code not in (429, 503) or attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)
            print(f"  [{code}] 재시도 {attempt + 1}/{max_retries} ({delay:.0f}s 대기)")
            await asyncio.sleep(delay)
        except httpx.TransportError as e:
            if attempt == max_retries - 1:
                raise
            delay = 2.0 * (2 ** attempt)
            print(f"  [네트워크 오류] {type(e).__name__}: {e} — 재시도 {attempt + 1}/{max_retries} ({delay:.0f}s 대기)")
            await asyncio.sleep(delay)


class LLMClient:
    _instance = None

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment")
        self.client = genai.Client(api_key=api_key)

    @classmethod
    def get_instance(cls) -> "LLMClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
