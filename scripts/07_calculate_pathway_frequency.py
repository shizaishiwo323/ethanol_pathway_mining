from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from utils.deepseek_client import load_config


ROOT = Path(__file__).resolve().parents[1]
PAPER_AI_PATH = ROOT / "05_statistics" / "paper_level_ai_summary.xlsx"
PAPER_RULE_PATH = ROOT / "05_statistics" / "paper_level_pathway_summary.xlsx"
RESOLVED_PATH = ROOT / "05_statistics" / "pathway_conflict_ai_resolved.xlsx"
OUTPUT_PATH = ROOT / "05_statistics" / "pathway_frequency_summary.xlsx"
AUDIT_PATH = ROOT / "05_statistics" / "frequency_audit_summary.xlsx"
PATHWAY_CODES = ["P1", "P2", "P3", "P4", "P5", "P6"]


def split_codes(value) -> set[str]:
    if pd.isna(value) or not str(value).strip():
        return set()
    return {item.strip() for item in str(value).split(";") if item.strip()}


def main() -> None:
    source_priority = "paper_level_ai_summary"
    if PAPER_AI_PATH.exists():
        df = pd.read_excel(PAPER_AI_PATH)
        if RESOLVED_PATH.exists():
            resolved = pd.read_excel(RESOLVED_PATH)
            decision_text = resolved.get("final_decision", pd.Series(dtype=str)).astype(str).str.strip()
            resolved = resolved[decision_text.ne("") & decision_text.str.lower().ne("nan")].copy()
            if not resolved.empty:
                source_priority = "conflict_resolved_over_paper_level_ai_summary"
            for _, row in resolved.iterrows():
                paper_id = row.get("paper_id")
                mask = df["paper_id"].eq(paper_id)
                if not mask.any():
                    continue
                decision = str(row.get("final_decision", "")).strip().lower()
                if decision == "exclude_from_final_statistics":
                    df.loc[mask, "final_include"] = "no"
                    continue
                if decision == "keep_paper_summary":
                    continue
                main = row.get("ai_resolved_main_pathway", "")
                mentioned = row.get("ai_resolved_mentioned_pathways", "")
                if str(main).strip() and str(main).lower() != "nan":
                    df.loc[mask, "final_main_pathways"] = main
                if str(mentioned).strip() and str(mentioned).lower() != "nan":
                    df.loc[mask, "final_mentioned_pathways"] = mentioned
                if decision == "use_resolved_result":
                    df.loc[mask, "final_include"] = "yes"
        mentioned_col = "final_mentioned_pathways"
        main_col = "final_main_pathways"
        rejected_col = "final_rejected_pathways"
        include_col = "final_include"
        ethanol_col = "ethanol_specific_level"
    else:
        df = pd.read_excel(PAPER_RULE_PATH)
        source_priority = "paper_level_pathway_summary_fallback"
        mentioned_col = "mentioned_pathways"
        main_col = "main_pathways"
        rejected_col = "rejected_pathways"
        include_col = "include_in_final_statistics"
        ethanol_col = ""

    valid = df[df[include_col].astype(str).str.lower().eq("yes")].copy() if include_col in df.columns else df.copy()
    total_valid = len(valid)
    rows = []
    for code in PATHWAY_CODES:
        mentioned_count = sum(code in split_codes(value) for value in valid.get(mentioned_col, []))
        main_count = sum(code in split_codes(value) for value in valid.get(main_col, []))
        rejected_count = sum(code in split_codes(value) for value in valid.get(rejected_col, []))
        if ethanol_col and ethanol_col in valid.columns:
            ethanol_specific_count = sum(
                code in split_codes(row.get(mentioned_col, "")) and str(row.get(ethanol_col, "")).lower() in {"yes", "partial"}
                for _, row in valid.iterrows()
            )
        else:
            ethanol_specific_count = mentioned_count
        rows.append(
            {
                "pathway_code": code,
                "mentioned_paper_count": int(mentioned_count),
                "main_paper_count": int(main_count),
                "rejected_paper_count": int(rejected_count),
                "ethanol_specific_count": int(ethanol_specific_count),
                "total_valid_papers": int(total_valid),
                "mentioned_ratio": mentioned_count / total_valid if total_valid else 0,
                "main_ratio": main_count / total_valid if total_valid else 0,
            }
        )

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_excel(OUTPUT_PATH, index=False)
    write_audit(source_priority, total_valid)
    print(f"Pathway frequency summary -> {OUTPUT_PATH.relative_to(ROOT)}")


def count_rows(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len(pd.read_excel(path))
    except ValueError:
        return 0


def count_review_source(source: str) -> int:
    review_path = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
    if not review_path.exists():
        return 0
    review = pd.read_excel(review_path)
    if "review_source" not in review.columns:
        return 0
    return int(review["review_source"].astype(str).eq(source).sum())


def write_audit(source_priority: str, total_valid: int) -> None:
    config = load_config()
    paper_failed = ROOT / "05_statistics" / "deepseek_paper_summary_failed.xlsx"
    conflict_failed = ROOT / "05_statistics" / "deepseek_conflict_resolution_failed.xlsx"
    conflict_report = ROOT / "05_statistics" / "pathway_conflict_report.xlsx"
    conflict_resolved = ROOT / "05_statistics" / "pathway_conflict_ai_resolved.xlsx"
    sentence_failed = ROOT / "04_extract_results" / "deepseek_review_failed_rows.xlsx"
    audit = pd.DataFrame(
        [
            {
                "run_timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "model_name": config.get("model", ""),
                "config_batch_size": config.get("batch_size", ""),
                "config_temperature": config.get("temperature", ""),
                "source_priority": source_priority,
                "n_total_papers": count_rows(PAPER_AI_PATH) or count_rows(PAPER_RULE_PATH),
                "n_final_include_yes": int(total_valid),
                "n_deepseek_sentence_reviewed_rows": count_review_source("deepseek") + count_review_source("deepseek_retry"),
                "n_fallback_not_sent_rows": count_review_source("fallback_not_sent"),
                "n_failed_sentence_rows": count_rows(sentence_failed),
                "n_deepseek_paper_summary_success": count_rows(PAPER_AI_PATH),
                "n_deepseek_paper_summary_failed": count_rows(paper_failed),
                "n_conflict_count": count_rows(conflict_report),
                "n_conflict_resolved": count_rows(conflict_resolved),
                "n_conflict_unresolved": count_rows(conflict_failed),
            }
        ]
    )
    audit.to_excel(AUDIT_PATH, index=False)


if __name__ == "__main__":
    main()
