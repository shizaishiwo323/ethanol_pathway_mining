from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "04_ai_pathway_review_results.xlsx"
METADATA_PATH = ROOT / "02_metadata" / "literature_metadata.xlsx"
OUTPUT_DIR = ROOT / "05_statistics"
OUTPUT_PATH = OUTPUT_DIR / "paper_level_pathway_summary.xlsx"
AI_SUMMARY_PATH = OUTPUT_DIR / "paper_level_ai_summary.xlsx"


def split_codes(value) -> list[str]:
    if pd.isna(value) or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split(";") if item.strip()]


def join_codes(codes: set[str]) -> str:
    return ";".join(sorted(codes))


def confidence_overall(values: pd.Series) -> str:
    normalized = {str(value).strip().lower() for value in values.dropna()}
    if "low" in normalized:
        return "low"
    if "medium" in normalized:
        return "medium"
    if "high" in normalized:
        return "high"
    return "low"


def summarize_group(paper_id: str, group: pd.DataFrame) -> dict:
    mentioned = set()
    main = set()
    compared = set()
    rejected = set()
    ethanol_specific = set()
    evidence_types = set()
    evidence_sentences = []
    included_confidences = []

    for _, row in group.iterrows():
        codes = set(split_codes(row.get("ai_final_pathway")))
        role = str(row.get("ai_role", "")).strip().lower()
        include = str(row.get("ai_include_in_statistics", "")).strip().lower() == "yes"
        ethanol = str(row.get("ai_ethanol_specific", "")).strip().lower()

        if not codes:
            continue
        if role in {"mention", "main", "compare"} and include:
            mentioned.update(codes)
            included_confidences.append(row.get("ai_confidence", ""))
        if role == "main" and include:
            main.update(codes)
            sentence = str(row.get("sentence", "")).strip()
            if sentence and len(evidence_sentences) < 5:
                evidence_sentences.append(sentence)
        if role == "compare" and include:
            compared.update(codes)
        if role == "reject":
            rejected.update(codes)
        if ethanol == "yes" and include:
            ethanol_specific.update(codes)
        evidence_type = str(row.get("ai_evidence_type", "")).strip()
        if evidence_type and evidence_type.lower() != "nan":
            evidence_types.add(evidence_type)

    low_confidence = any(str(value).strip().lower() == "low" for value in included_confidences)
    pathway_summary = []
    if main:
        pathway_summary.append(f"main={join_codes(main)}")
    if mentioned - main:
        pathway_summary.append(f"mentioned_only={join_codes(mentioned - main)}")
    if rejected:
        pathway_summary.append(f"rejected={join_codes(rejected)}")

    return {
        "paper_id": paper_id,
        "txt_name": ";".join(sorted(set(group.get("txt_name", pd.Series(dtype=str)).dropna().astype(str)))),
        "mentioned_pathways": join_codes(mentioned),
        "main_pathways": join_codes(main),
        "compared_pathways": join_codes(compared),
        "rejected_pathways": join_codes(rejected),
        "ethanol_specific_pathways": join_codes(ethanol_specific),
        "evidence_types": ";".join(sorted(evidence_types)),
        "key_evidence_sentences": " || ".join(evidence_sentences),
        "pathway_decision_summary": "; ".join(pathway_summary),
        "low_confidence_flags": "yes" if low_confidence else "no",
        "confidence_overall": confidence_overall(pd.Series(included_confidences)),
        "include_in_final_statistics": "yes" if mentioned or main else "no",
    }


def build_ai_summary(summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in summary.iterrows():
        final_main = str(row.get("main_pathways", "")).strip()
        final_mentioned = str(row.get("mentioned_pathways", "")).strip()
        evidence = str(row.get("evidence_types", "")).strip()
        confidence = str(row.get("confidence_overall", "low")).strip() or "low"
        ethanol_level = "yes" if str(row.get("ethanol_specific_pathways", "")).strip() else "unclear"
        if final_main:
            reason = f"Sentence-level AI review found main-pathway evidence for {final_main}."
        elif final_mentioned:
            reason = f"Sentence-level AI review found pathway mentions for {final_mentioned}, but no main-pathway claim."
        else:
            reason = "No included sentence-level pathway evidence after AI review."
        rows.append(
            {
                "paper_id": row["paper_id"],
                "final_mentioned_pathways": final_mentioned,
                "final_main_pathways": final_main,
                "final_rejected_pathways": row.get("rejected_pathways", ""),
                "ethanol_specific_level": ethanol_level,
                "main_evidence_basis": evidence or "unknown",
                "ai_paper_reason": reason,
                "ai_paper_confidence": confidence,
                "final_include": row.get("include_in_final_statistics", "no"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    summary = pd.DataFrame([summarize_group(paper_id, group) for paper_id, group in df.groupby("paper_id")])

    if METADATA_PATH.exists():
        metadata = pd.read_excel(METADATA_PATH)
        metadata_cols = [col for col in ["paper_id", "pdf_name", "title", "year", "doi", "reaction_type", "catalyst"] if col in metadata.columns]
        summary = metadata[metadata_cols].merge(summary, on="paper_id", how="right")

    OUTPUT_DIR.mkdir(exist_ok=True)
    summary.to_excel(OUTPUT_PATH, index=False)
    build_ai_summary(summary).to_excel(AI_SUMMARY_PATH, index=False)
    print(f"Paper-level pathway summary: {len(summary)} rows -> {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"Paper-level AI summary -> {AI_SUMMARY_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
