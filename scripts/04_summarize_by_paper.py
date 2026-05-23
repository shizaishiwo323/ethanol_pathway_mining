from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "05_manual_check" / "manual_check.xlsx"
OUTPUT_PATH = ROOT / "05_manual_check" / "paper_level_summary.xlsx"


def split_codes(value) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def join_codes(codes: set[str]) -> str:
    return ";".join(sorted(codes))


def summarize_group(paper_id: str, group: pd.DataFrame) -> dict:
    mentioned = set()
    main = set()
    rejected = set()
    evidence = []

    for _, row in group.iterrows():
        codes = split_codes(row.get("manual_pathway"))
        role = str(row.get("role", "")).strip().lower()
        if not codes:
            continue
        if role != "reject":
            mentioned.update(codes)
        if role == "main":
            main.update(codes)
        if role == "reject":
            rejected.update(codes)
        if len(evidence) < 3:
            evidence.append(str(row.get("sentence", "")).strip())

    return {
        "paper_id": paper_id,
        "mentioned_pathways": join_codes(mentioned),
        "main_pathway": join_codes(main),
        "rejected_pathway": join_codes(rejected),
        "evidence_sentence_count": int(group["sentence"].notna().sum()),
        "pathway_sentence": " || ".join(item for item in evidence if item),
        "manual_checked": "yes" if mentioned or main or rejected else "no",
    }


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    if df.empty:
        out = pd.DataFrame(
            columns=[
                "paper_id",
                "mentioned_pathways",
                "main_pathway",
                "rejected_pathway",
                "evidence_sentence_count",
                "pathway_sentence",
                "manual_checked",
            ]
        )
    else:
        out = pd.DataFrame([summarize_group(paper_id, group) for paper_id, group in df.groupby("paper_id")])

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    out.to_excel(OUTPUT_PATH, index=False)
    print(f"Paper-level summary rows: {len(out)} -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
