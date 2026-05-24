from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
BATCH_DIR = ROOT / "04_extract_results" / "ai_review_batches"
OUTPUT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
REQUIRED_COLUMNS = [
    "paper_id",
    "sentence_id",
    "sentence",
    "rule_matched_pathways",
    "ai_final_pathway",
    "ai_role",
    "ai_ethanol_specific",
    "ai_evidence_type",
    "ai_evidence_reason",
    "ai_confidence",
    "ai_include_in_statistics",
]


def main() -> None:
    files = sorted(BATCH_DIR.glob("*_reviewed.xlsx"))
    if not files:
        raise FileNotFoundError(f"No reviewed batch files found in {BATCH_DIR}")

    df = pd.concat([pd.read_excel(path) for path in files], ignore_index=True)
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Reviewed batches are missing columns: {missing}")

    duplicate_count = df.duplicated(["paper_id", "sentence_id"]).sum()
    blank_counts = df[REQUIRED_COLUMNS].isna().sum().to_dict()

    df.to_excel(OUTPUT_PATH, index=False)
    print(f"Merged reviewed rows: {len(df)} -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Duplicate paper_id + sentence_id rows: {duplicate_count}")
    print(f"Blank required-field counts: {blank_counts}")


if __name__ == "__main__":
    main()
