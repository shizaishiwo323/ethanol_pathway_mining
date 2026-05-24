import json
import time
from pathlib import Path

import pandas as pd

from utils.deepseek_client import append_jsonl, as_code_string, call_json, get_client, load_config


ROOT = Path(__file__).resolve().parents[1]
CONFLICT_PATH = ROOT / "05_statistics" / "pathway_conflict_report.xlsx"
SENTENCE_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
PAPER_PATH = ROOT / "05_statistics" / "paper_level_ai_summary.xlsx"
PROMPT_PATH = ROOT / "00_project_notes" / "ai_conflict_resolution_prompt.md"
OUTPUT_PATH = ROOT / "05_statistics" / "pathway_conflict_ai_resolved.xlsx"
RAW_PATH = ROOT / "05_statistics" / "deepseek_conflict_resolution_raw_jsonl.jsonl"
FAILED_PATH = ROOT / "05_statistics" / "deepseek_conflict_resolution_failed.xlsx"

REQUIRED_FIELDS = [
    "paper_id",
    "conflict_type",
    "ai_resolved_main_pathway",
    "ai_resolved_mentioned_pathways",
    "ai_resolution_reason",
    "final_decision",
]


def build_user_prompt(conflict_row: pd.Series, sentence_group: pd.DataFrame, paper_row: dict) -> str:
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
        "conflict": conflict_row.to_dict(),
        "paper_level_summary": paper_row,
        "sentence_level_reviews": sentence_records,
    }
    return "Please resolve this conflict and output valid json only:\n" + json.dumps(payload, ensure_ascii=False, default=str)


def normalize_result(conflict_row: pd.Series, result: dict) -> dict:
    missing = [field for field in REQUIRED_FIELDS if field not in result]
    if missing:
        raise ValueError(f"Missing fields in DeepSeek conflict resolution: {missing}")
    return {
        "paper_id": conflict_row.get("paper_id", result.get("paper_id", "")),
        "conflict_type": conflict_row.get("conflict_type", result.get("conflict_type", "")),
        "original_sentence_level_result": conflict_row.get("original_sentence_level_result", ""),
        "original_paper_level_result": conflict_row.get("original_paper_level_result", ""),
        "ai_resolved_main_pathway": as_code_string(result.get("ai_resolved_main_pathway")),
        "ai_resolved_mentioned_pathways": as_code_string(result.get("ai_resolved_mentioned_pathways")),
        "ai_resolution_reason": str(result.get("ai_resolution_reason", "")).strip(),
        "final_decision": str(result.get("final_decision", "")).strip(),
    }


def main() -> None:
    config = load_config()
    client = get_client(config)
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    conflicts = pd.read_excel(CONFLICT_PATH)
    if conflicts.empty:
        columns = [
            "paper_id",
            "conflict_type",
            "original_sentence_level_result",
            "original_paper_level_result",
            "ai_resolved_main_pathway",
            "ai_resolved_mentioned_pathways",
            "ai_resolution_reason",
            "final_decision",
        ]
        pd.DataFrame(columns=columns).to_excel(OUTPUT_PATH, index=False)
        pd.DataFrame().to_excel(FAILED_PATH, index=False)
        print("No conflicts to resolve.")
        return
    sentence_df = pd.read_excel(SENTENCE_PATH)
    paper_df = pd.read_excel(PAPER_PATH)
    sentence_by_paper = {paper_id: group for paper_id, group in sentence_df.groupby("paper_id")}
    paper_by_id = paper_df.set_index("paper_id")
    rows = []
    failures = []

    if RAW_PATH.exists():
        RAW_PATH.unlink()

    for _, conflict_row in conflicts.iterrows():
        paper_id = conflict_row.get("paper_id", "")
        try:
            sentence_group = sentence_by_paper.get(paper_id, pd.DataFrame(columns=sentence_df.columns))
            paper_row = paper_by_id.loc[paper_id].to_dict() if paper_id in paper_by_id.index else {}
            parsed, raw = call_json(client, config, system_prompt, build_user_prompt(conflict_row, sentence_group, paper_row))
            append_jsonl(RAW_PATH, {"paper_id": paper_id, "conflict_type": conflict_row.get("conflict_type", ""), "parsed": parsed, "raw": raw})
            rows.append(normalize_result(conflict_row, parsed))
        except Exception as exc:
            failed = conflict_row.to_dict()
            failed["error"] = str(exc)
            failures.append(failed)
        time.sleep(float(config.get("sleep_seconds", 0.5)))

    pd.DataFrame(rows).to_excel(OUTPUT_PATH, index=False)
    pd.DataFrame(failures).to_excel(FAILED_PATH, index=False)
    print(f"DeepSeek conflict resolutions: {len(rows)} -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Failed conflicts: {len(failures)} -> {FAILED_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
