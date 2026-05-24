import json
import os
import time
from pathlib import Path
from typing import Any

from openai import OpenAI


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = {
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-v4-flash",
    "temperature": 0,
    "max_tokens": 6000,
    "batch_size": 10,
    "sleep_seconds": 0.5,
    "max_retries": 3,
    "request_timeout_seconds": 60,
    "max_sentence_chars": 1600,
    "max_context_chars": 800,
}


def load_config(path: Path | None = None) -> dict[str, Any]:
    config = DEFAULT_CONFIG.copy()
    config_path = path or ROOT / "config" / "deepseek_config.json"
    if config_path.exists():
        with config_path.open(encoding="utf-8") as f:
            config.update(json.load(f))
    return config


def get_client(config: dict[str, Any]) -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is not set. Export it before running DeepSeek scripts.")
    return OpenAI(api_key=api_key, base_url=config["base_url"])


def parse_json_object(content: str) -> dict[str, Any]:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def call_json(
    client: OpenAI,
    config: dict[str, Any],
    system_prompt: str,
    user_prompt: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    last_error = None
    for attempt in range(1, int(config.get("max_retries", 3)) + 1):
        try:
            response = client.chat.completions.create(
                model=config["model"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=config.get("temperature", 0),
                max_tokens=config.get("max_tokens", 1200),
                response_format={"type": "json_object"},
                stream=False,
                timeout=float(config.get("request_timeout_seconds", 60)),
            )
            content = response.choices[0].message.content or ""
            if not content.strip():
                raise ValueError("empty model content")
            parsed = parse_json_object(content)
            raw = response.model_dump() if hasattr(response, "model_dump") else json.loads(response.model_dump_json())
            return parsed, raw
        except Exception as exc:
            last_error = exc
            if attempt < int(config.get("max_retries", 3)):
                time.sleep(float(config.get("sleep_seconds", 0.5)) * attempt)
    raise RuntimeError(f"DeepSeek JSON call failed: {last_error}") from last_error


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def as_code_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ";".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()
