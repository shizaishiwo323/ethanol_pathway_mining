import json
import time
from pathlib import Path

import pandas as pd

from utils.deepseek_client import append_jsonl, as_code_string, call_json, get_client, load_config


ROOT = Path(__file__).resolve().parents[1]
SENTENCE_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
PAPER_SUMMARY_PATH = ROOT / "05_statistics" / "paper_level_pathway_summary.xlsx"
METADATA_PATH = ROOT / "02_metadata" / "literature_metadata.xlsx"
PROMPT_PATH = ROOT / "00_project_notes" / "ai_paper_level_summary_prompt.md"
OUTPUT_PATH = ROOT / "05_statistics" / "paper_level_ai_summary.xlsx"
RAW_PATH = ROOT / "05_statistics" / "deepseek_paper_summary_raw_jsonl.jsonl"
FAILED_PATH = ROOT / "05_statistics" / "deepseek_paper_summary_failed.xlsx"

REQUIRED_FIELDS = [
    "paper_id",
    "final_mentioned_pathways",
    "final_main_pathways",
    "final_rejected_pathways",
    "ethanol_specific_level",
    "main_evidence_basis",
    "ai_paper_reason",
    "ai_paper_confidence",
    "final_include",
]


def load_metadata() -> pd.DataFrame:
    if METADATA_PATH.exists():
        return pd.read_excel(METADATA_PATH)
    return pd.DataFrame(columns=["paper_id"])


def build_user_prompt(paper_id: str, sentence_group: pd.DataFrame, paper_row: dict, metadata_row: dict) -> str:
    relevant = sentence_group[
        sentence_group["ai_role"].astype(str).str.lower().isin(["main", "compare", "reject", "mention"])
        | sentence_group["ai_include_in_statistics"].astype(str).str.lower().eq("yes")
    ].copy()
    sentence_records = relevant[
        [
            "sentence_id",
            "sentence",
            "ai_final_pathway",
            "ai_role",
            "ai_ethanol_specific",
            "ai_evidence_type",
            "ai_evidence_reason",
            "ai_confidence",
            "ai_include_in_statistics",
        ]
    ].to_dict(orient="records")
    payload = {
        "paper_id": paper_id,
        "metadata": metadata_row,
        "rule_aggregated_paper_summary": paper_row,
        "sentence_level_reviews": sentence_records,
    }
    return "Please summarize this paper and output valid json only:\n" + json.dumps(payload, ensure_ascii=False, default=str)


def normalize_result(paper_id: str, result: dict) -> dict:
    missing = [field for field in REQUIRED_FIELDS if field not in result]
    if missing:
        raise ValueError(f"Missing fields in DeepSeek paper summary: {missing}")
    return {
        "paper_id": paper_id,
        "final_mentioned_pathways": as_code_string(result.get("final_mentioned_pathways")),
        "final_main_pathways": as_code_string(result.get("final_main_pathways")),
        "final_rejected_pathways": as_code_string(result.get("final_rejected_pathways")),
        "ethanol_specific_level": str(result.get("ethanol_specific_level", "")).strip(),
        "main_evidence_basis": as_code_string(result.get("main_evidence_basis")),
        "ai_paper_reason": str(result.get("ai_paper_reason", "")).strip(),
        "ai_paper_confidence": str(result.get("ai_paper_confidence", "")).strip(),
        "final_include": str(result.get("final_include", "")).strip(),
    }


def main() -> None:
    config = load_config()
    client = get_client(config)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    sentence_df = pd.read_excel(SENTENCE_PATH)
    paper_df = pd.read_excel(PAPER_SUMMARY_PATH)
    metadata = load_metadata()
    paper_by_id = paper_df.set_index("paper_id")
    metadata_by_id = metadata.set_index("paper_id") if "paper_id" in metadata.columns else pd.DataFrame()
    rows = []
    failures = []

    if RAW_PATH.exists():
        RAW_PATH.unlink()

    for paper_id, group in sentence_df.groupby("paper_id"):
        try:
            paper_row = paper_by_id.loc[paper_id].to_dict() if paper_id in paper_by_id.index else {}
            metadata_row = metadata_by_id.loc[paper_id].to_dict() if paper_id in metadata_by_id.index else {}
            parsed, raw = call_json(client, config, system_prompt, build_user_prompt(paper_id, group, paper_row, metadata_row))
            append_jsonl(RAW_PATH, {"paper_id": paper_id, "parsed": parsed, "raw": raw})
            rows.append(normalize_result(paper_id, parsed))
        except Exception as exc:
            failures.append({"paper_id": paper_id, "error": str(exc)})
        time.sleep(float(config.get("sleep_seconds", 0.5)))

    pd.DataFrame(rows).to_excel(OUTPUT_PATH, index=False)
    pd.DataFrame(failures).to_excel(FAILED_PATH, index=False)
    print(f"DeepSeek paper summaries: {len(rows)} -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Failed papers: {len(failures)} -> {FAILED_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
