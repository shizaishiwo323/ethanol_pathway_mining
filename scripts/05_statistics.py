from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "05_manual_check" / "paper_level_summary.xlsx"
OUTPUT_PATH = ROOT / "04_extract_results" / "pathway_frequency_summary.xlsx"
PATHWAY_CODES = ["P1", "P2", "P3", "P4", "P5", "P6"]


def split_codes(value) -> set[str]:
    if pd.isna(value) or not str(value).strip():
        return set()
    return {item.strip() for item in str(value).split(";") if item.strip()}


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    rows = []
    for code in PATHWAY_CODES:
        mentioned_count = sum(code in split_codes(value) for value in df.get("mentioned_pathways", []))
        main_count = sum(code in split_codes(value) for value in df.get("main_pathway", []))
        rejected_count = sum(code in split_codes(value) for value in df.get("rejected_pathway", []))
        rows.append(
            {
                "pathway_code": code,
                "mentioned_count": int(mentioned_count),
                "main_count": int(main_count),
                "rejected_count": int(rejected_count),
            }
        )

    out = pd.DataFrame(rows)
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    out.to_excel(OUTPUT_PATH, index=False)
    print(f"Frequency summary -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
