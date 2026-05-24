from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "03_rule_pathway_matches.xlsx"
OUTPUT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_input.xlsx"
BATCH_DIR = ROOT / "04_extract_results" / "ai_review_batches"
BATCH_SIZE = 150


REVIEW_COLUMNS = [
    "paper_id",
    "txt_name",
    "sentence_id",
    "sentence",
    "rule_matched_pathways",
    "matched_keywords",
    "ethanol_specific",
    "oxygenate_related",
]


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    df = df[df["needs_ai_review"].astype(str).str.lower().eq("yes")].copy()
    out = df[[col for col in REVIEW_COLUMNS if col in df.columns]].copy()

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    out.to_excel(OUTPUT_PATH, index=False)

    BATCH_DIR.mkdir(exist_ok=True)
    for idx, start in enumerate(range(0, len(out), BATCH_SIZE), start=1):
        batch = out.iloc[start : start + BATCH_SIZE].copy()
        batch.to_excel(BATCH_DIR / f"batch_{idx:03d}.xlsx", index=False)

    print(f"AI review input: {len(out)} rows -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Batches written -> {BATCH_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
