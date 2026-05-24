import json
import time
from pathlib import Path

import pandas as pd

from utils.deepseek_client import append_jsonl, as_code_string, call_json, get_client, load_config


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_input.xlsx"
PROMPT_PATH = ROOT / "00_project_notes" / "ai_pathway_review_prompt.md"
OUTPUT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
RAW_PATH = ROOT / "04_extract_results" / "deepseek_review_raw_jsonl.jsonl"
FAILED_PATH = ROOT / "04_extract_results" / "deepseek_review_failed_rows.xlsx"

REQUIRED_FIELDS = [
    "paper_id",
    "sentence_id",
    "ai_final_pathway",
    "ai_role",
    "ai_ethanol_specific",
    "ai_evidence_type",
    "ai_evidence_reason",
    "ai_confidence",
    "ai_include_in_statistics",
]


def clip_text(value, max_chars: int) -> str:
    text = "" if pd.isna(value) else str(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars // 2] + "\n...[truncated]...\n" + text[-max_chars // 2 :]


def row_payload(row: pd.Series, config: dict) -> dict:
    max_sentence = int(config.get("max_sentence_chars", 1600))
    max_context = int(config.get("max_context_chars", 800))
    return {
        "paper_id": row.get("paper_id", ""),
        "txt_name": row.get("txt_name", ""),
        "sentence_id": row.get("sentence_id", ""),
        "page": row.get("page", ""),
        "previous_sentence": clip_text(row.get("previous_sentence", ""), max_context),
        "sentence": clip_text(row.get("sentence", ""), max_sentence),
        "next_sentence": clip_text(row.get("next_sentence", ""), max_context),
        "rule_matched_pathways": row.get("rule_matched_pathways", ""),
        "matched_keywords": row.get("matched_keywords", ""),
        "ethanol_specific": row.get("ethanol_specific", ""),
        "oxygenate_related": row.get("oxygenate_related", ""),
    }


def build_user_prompt(batch: pd.DataFrame, config: dict) -> str:
    payload = {
        "task": "Review each row and return one result per row.",
        "output_json_schema": {
            "results": [
                {
                    "paper_id": "E001",
                    "sentence_id": "S0001",
                    "ai_final_pathway": ["P1"],
                    "ai_role": "main",
                    "ai_ethanol_specific": "yes",
                    "ai_evidence_type": "DFT",
                    "ai_evidence_reason": "Short reason.",
                    "ai_confidence": "high",
                    "ai_include_in_statistics": "yes",
                }
            ]
        },
        "rows": [row_payload(row, config) for _, row in batch.iterrows()],
    }
    return "Please review these rows and output valid json only:\n" + json.dumps(payload, ensure_ascii=False, default=str)


def normalize_result(row: pd.Series, result: dict) -> dict:
    missing = [field for field in REQUIRED_FIELDS if field not in result]
    if missing:
        raise ValueError(f"Missing fields in DeepSeek result: {missing}")
    return {
        "paper_id": row.get("paper_id", result.get("paper_id", "")),
        "txt_name": row.get("txt_name", ""),
        "sentence_id": row.get("sentence_id", result.get("sentence_id", "")),
        "sentence": row.get("sentence", ""),
        "rule_matched_pathways": row.get("rule_matched_pathways", ""),
        "matched_keywords": row.get("matched_keywords", ""),
        "ai_final_pathway": as_code_string(result.get("ai_final_pathway")),
        "ai_role": str(result.get("ai_role", "")).strip(),
        "ai_ethanol_specific": str(result.get("ai_ethanol_specific", "")).strip(),
        "ai_evidence_type": as_code_string(result.get("ai_evidence_type")),
        "ai_evidence_reason": str(result.get("ai_evidence_reason", "")).strip(),
        "ai_confidence": str(result.get("ai_confidence", "")).strip(),
        "ai_include_in_statistics": str(result.get("ai_include_in_statistics", "")).strip(),
        "review_source": "deepseek",
    }


def fallback_result(row: pd.Series, reason: str) -> dict:
    return {
        "paper_id": row.get("paper_id", ""),
        "txt_name": row.get("txt_name", ""),
        "sentence_id": row.get("sentence_id", ""),
        "sentence": row.get("sentence", ""),
        "rule_matched_pathways": row.get("rule_matched_pathways", ""),
        "matched_keywords": row.get("matched_keywords", ""),
        "ai_final_pathway": "",
        "ai_role": "unclear",
        "ai_ethanol_specific": "unclear",
        "ai_evidence_type": "unknown",
        "ai_evidence_reason": reason,
        "ai_confidence": "low",
        "ai_include_in_statistics": "no",
        "review_source": "fallback_not_sent",
    }


def needs_deepseek(row: pd.Series) -> bool:
    rule_paths = str(row.get("rule_matched_pathways", "") or "").strip()
    high_mechanism = (
        str(row.get("relevance_level", "")).strip().lower() == "high"
        and str(row.get("sentence_type", "")).strip().lower() == "mechanism"
    )
    return bool(rule_paths and rule_paths.lower() != "nan") or high_mechanism


def main() -> None:
    config = load_config()
    client = get_client(config)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    df = pd.read_excel(INPUT_PATH)
    to_review = df[df.apply(needs_deepseek, axis=1)].copy()
    skipped = df[~df.apply(needs_deepseek, axis=1)].copy()
    rows = []
    failures = []

    if RAW_PATH.exists():
        RAW_PATH.unlink()

    for _, row in skipped.iterrows():
        rows.append(fallback_result(row, "No pathway keyword match or high-relevance mechanism signal; not sent to DeepSeek."))

    batch_size = int(config.get("batch_size", 10))
    for start in range(0, len(to_review), batch_size):
        batch = to_review.iloc[start : start + batch_size].copy()
        try:
            parsed, raw = call_json(client, config, system_prompt, build_user_prompt(batch, config))
            batch_results = parsed.get("results")
            if not isinstance(batch_results, list):
                raise ValueError("DeepSeek batch response must contain a results list")
            append_jsonl(
                RAW_PATH,
                {
                    "batch_start": int(start),
                    "batch_size": int(len(batch)),
                    "parsed": parsed,
                    "raw": raw,
                },
            )
            by_key = {
                (str(result.get("paper_id", "")), str(result.get("sentence_id", ""))): result
                for result in batch_results
                if isinstance(result, dict)
            }
            for _, row in batch.iterrows():
                key = (str(row.get("paper_id", "")), str(row.get("sentence_id", "")))
                if key not in by_key:
                    raise ValueError(f"Missing result for {key}")
                rows.append(normalize_result(row, by_key[key]))
        except Exception as exc:
            for _, row in batch.iterrows():
                failed = row.to_dict()
                failed["error"] = str(exc)
                failures.append(failed)
                rows.append(fallback_result(row, f"DeepSeek batch failed: {exc}"))
        time.sleep(float(config.get("sleep_seconds", 0.5)))

    pd.DataFrame(rows).to_excel(OUTPUT_PATH, index=False)
    pd.DataFrame(failures).to_excel(FAILED_PATH, index=False)
    print(f"DeepSeek sentence review rows: {len(rows)} -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Rows sent to DeepSeek: {len(to_review)}; fallback rows not sent: {len(skipped)}")
    print(f"Failed rows: {len(failures)} -> {FAILED_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
