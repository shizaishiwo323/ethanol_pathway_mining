from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SENTENCE_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
PAPER_PATH = ROOT / "05_statistics" / "paper_level_ai_summary.xlsx"
OUTPUT_PATH = ROOT / "05_statistics" / "pathway_conflict_report.xlsx"
RESOLVED_PATH = ROOT / "05_statistics" / "pathway_conflict_ai_resolved.xlsx"


def split_codes(value) -> set[str]:
    if pd.isna(value) or not str(value).strip():
        return set()
    return {item.strip() for item in str(value).split(";") if item.strip()}


def add_conflict(rows: list[dict], paper_id: str, conflict_type: str, sentence_result: str, paper_result: str) -> None:
    rows.append(
        {
            "paper_id": paper_id,
            "conflict_type": conflict_type,
            "original_sentence_level_result": sentence_result,
            "original_paper_level_result": paper_result,
        }
    )


def main() -> None:
    sentence_df = pd.read_excel(SENTENCE_PATH)
    paper_df = pd.read_excel(PAPER_PATH)
    paper_by_id = paper_df.set_index("paper_id")
    rows = []

    for paper_id, group in sentence_df.groupby("paper_id"):
        paper_row = paper_by_id.loc[paper_id] if paper_id in paper_by_id.index else pd.Series(dtype=object)
        main_codes = set()
        reject_codes = set()
        low_include = 0
        no_ethanol_include = 0

        for _, row in group.iterrows():
            codes = split_codes(row.get("ai_final_pathway"))
            role = str(row.get("ai_role", "")).strip().lower()
            include = str(row.get("ai_include_in_statistics", "")).strip().lower() == "yes"
            ethanol = str(row.get("ai_ethanol_specific", "")).strip().lower()
            confidence = str(row.get("ai_confidence", "")).strip().lower()
            if role == "main" and include:
                main_codes.update(codes)
            if role == "reject":
                reject_codes.update(codes)
            if include and ethanol == "no":
                no_ethanol_include += 1
            if include and confidence == "low":
                low_include += 1

        if len(main_codes) > 1:
            add_conflict(rows, paper_id, "multiple_main_pathways", ";".join(sorted(main_codes)), str(paper_row.to_dict()))
        overlap = main_codes & reject_codes
        if overlap:
            add_conflict(rows, paper_id, "same_pathway_main_and_reject", ";".join(sorted(overlap)), str(paper_row.to_dict()))
        paper_main = split_codes(paper_row.get("final_main_pathways", ""))
        if main_codes and not main_codes.issubset(paper_main):
            add_conflict(rows, paper_id, "sentence_main_missing_from_paper_summary", ";".join(sorted(main_codes)), ";".join(sorted(paper_main)))
        if no_ethanol_include:
            add_conflict(rows, paper_id, "ethanol_no_but_included", f"{no_ethanol_include} included rows", str(paper_row.to_dict()))
        if low_include:
            add_conflict(rows, paper_id, "low_confidence_but_included", f"{low_include} included rows", str(paper_row.to_dict()))

    out = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    out.to_excel(OUTPUT_PATH, index=False)

    resolved = out.copy()
    for col in [
        "ai_resolved_main_pathway",
        "ai_resolved_mentioned_pathways",
        "ai_resolution_reason",
        "final_decision",
    ]:
        resolved[col] = ""
    resolved.to_excel(RESOLVED_PATH, index=False)

    print(f"Conflict rows: {len(out)} -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Conflict resolution template -> {RESOLVED_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
