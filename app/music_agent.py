"""Music Mood Agent — gợi nhạc theo tâm trạng người dùng.

Dùng Google Gemini API (google-genai SDK). Ưu tiên nhạc Việt/Anh,
hỗ trợ quốc gia khác khi yêu cầu.
"""

from __future__ import annotations

import logging
import os

from google import genai
from google.genai import types

from utils.mock_llm import ask_llm as mock_ask_llm

from .config import get_settings

logger = logging.getLogger(__name__)

PRICE_INPUT_PER_1K = 0.0001
PRICE_OUTPUT_PER_1K = 0.0004

SYSTEM_PROMPT = """\
Bạn là một chuyên gia âm nhạc đa ngôn ngữ. Nhiệm vụ:

1. Phân tích tâm trạng/cảm xúc từ tin nhắn người dùng.
2. Gợi ý 3-5 bài nhạc phù hợp với tâm trạng đó.
3. Ưu tiên nhạc Việt Nam và tiếng Anh, trừ khi người dùng yêu cầu ngôn ngữ/quốc gia khác.
4. Mỗi bài ghi rõ: Tên bài - Nghệ sĩ (Ngôn ngữ/Quốc gia).
5. Giải thích ngắn gọn vì sao chọn bài đó cho tâm trạng này.
6. Nếu người dùng nhắn không liên quan đến nhạc/cảm xúc, hãy hỏi lại tâm trạng.

Trả lời bằng cùng ngôn ngữ người dùng dùng. Format đẹp, dễ đọc.
"""


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


_client = None


def _get_client() -> genai.Client | None:
    global _client
    if _client is None:
        api_key = get_settings().gemini_api_key
        if not api_key:
            return None
        _client = genai.Client(api_key=api_key)
    return _client


def ask_llm(question: str, history: list[dict] | None = None) -> dict:
    """Gọi Gemini để gợi nhạc. Thử lần lượt các model phổ biến."""
    client = _get_client()
    if client is None:
        return mock_ask_llm(question, history)

    history = history or []

    # Xây dựng prompt kèm lịch sử hội thoại dạng text đơn giản, tương thích 100% SDK
    prompt_sections = []
    if history:
        prompt_sections.append("Lịch sử hội thoại trước đó:")
        for turn in history:
            role_label = "Người dùng" if turn.get("role") == "user" else "Trợ lý âm nhạc"
            prompt_sections.append(f"{role_label}: {turn.get('content', '')}")
        prompt_sections.append("\nTin nhắn mới nhất của người dùng:")
    prompt_sections.append(question)
    full_prompt = "\n".join(prompt_sections)

    # Thử model được cấu hình trước, sau đó fallback sang các model ổn định có trong tài khoản
    preferred_model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    fallback_models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-2.5-pro"]
    models_to_try = []
    for m in [preferred_model] + fallback_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                ),
            )
            answer = response.text
            if not answer:
                continue

            usage = getattr(response, "usage_metadata", None)
            if usage:
                t_in = usage.prompt_token_count
                t_out = usage.candidates_token_count
            else:
                t_in = _estimate_tokens(full_prompt)
                t_out = _estimate_tokens(answer)

            cost = t_in / 1000 * PRICE_INPUT_PER_1K + t_out / 1000 * PRICE_OUTPUT_PER_1K
            return {
                "answer": answer,
                "tokens_in": t_in,
                "tokens_out": t_out,
                "cost_usd": round(cost, 8),
            }
        except Exception as exc:
            last_error = exc
            logger.warning("Thử model %s thất bại: %s", model_name, exc)
            continue

    # Nếu tất cả model đều lỗi, trả về thông báo lỗi cụ thể để dễ chẩn đoán
    err_msg = (
        f"⚠️ Không thể kết nối Gemini API (Lỗi: {last_error}).\n\n"
        f"Vui lòng kiểm tra lại GEMINI_API_KEY hoặc quyền truy cập của key."
    )
    return {
        "answer": err_msg,
        "tokens_in": _estimate_tokens(full_prompt),
        "tokens_out": _estimate_tokens(err_msg),
        "cost_usd": 0.0,
    }
