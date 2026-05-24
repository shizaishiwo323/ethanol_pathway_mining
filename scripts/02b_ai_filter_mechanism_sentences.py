import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "04_extract_results" / "extracted_mechanism_sentences.xlsx"
LABELED_ALL_PATH = ROOT / "04_extract_results" / "ai_mechanism_sentence_labeled_all.xlsx"
CANDIDATES_PATH = ROOT / "04_extract_results" / "ai_mechanism_sentence_candidates.xlsx"
QUALITY_REPORT_PATH = ROOT / "04_extract_results" / "extraction_quality_report.xlsx"
CONVERSION_LOG_PATH = ROOT / "04_extract_results" / "pdf_conversion_log.xlsx"

MECHANISM_RE = re.compile(
    r"\b(mechanism|pathway|route|intermediate|dimerization|coupling|"
    r"rate[- ]determining|transition state|formation path|C[-–]C)\b",
    flags=re.IGNORECASE,
)
ETHANOL_RE = re.compile(r"\b(ethanol|C2H5OH)\b", flags=re.IGNORECASE)
OXYGENATE_RE = re.compile(r"\b(C2\+ oxygenates?|oxygenates?)\b", flags=re.IGNORECASE)
PATHWAY_RE = re.compile(
    r"(\*?OCCO|\*?COCO|\*?CHO|\*?COH|\*?OCHO|HCOO|formate|\*?CHx|\*?CH2|\*?CH3)",
    flags=re.IGNORECASE,
)
EVIDENCE_RE = re.compile(
    r"\b(DFT|density functional theory|free energy|energy barrier|barrier|"
    r"in situ|operando|Raman|FTIR|isotope|calculation|calculations|spectroscopy|adsorption energy)\b",
    flags=re.IGNORECASE,
)
PERFORMANCE_RE = re.compile(r"\b(Faradaic|FE|selectivity|current density|partial current|yield|production rate)\b", re.I)
NOISE_RE = re.compile(r"^(references|acknowledg|author contributions|competing interests)\b", re.I)


def joined_context(row: pd.Series) -> str:
    return " ".join(
        str(row.get(column, "") or "")
        for column in ["previous_sentence", "sentence", "next_sentence"]
    )


def classify_row(row: pd.Series) -> dict[str, str | int]:
    context = joined_context(row)
    sentence = str(row.get("sentence", "") or "")
    score = int(row.get("keyword_score", 0) or 0)

    has_ethanol = bool(ETHANOL_RE.search(context))
    has_oxygenate = bool(OXYGENATE_RE.search(context))
    has_mechanism = bool(MECHANISM_RE.search(context))
    has_pathway = bool(PATHWAY_RE.search(context))
    has_evidence = bool(EVIDENCE_RE.search(context))
    is_performance = bool(PERFORMANCE_RE.search(sentence)) and not has_mechanism
    is_noise = len(sentence) < 45 or bool(NOISE_RE.search(sentence))

    semantic_score = score
    if has_ethanol:
        semantic_score += 3
    elif has_oxygenate:
        semantic_score += 1
    if has_mechanism:
        semantic_score += 3
    if has_pathway:
        semantic_score += 3
    if has_evidence:
        semantic_score += 2
    if is_performance:
        semantic_score -= 3
    if is_noise:
        semantic_score -= 5

    if is_noise:
        ai_relevant = "no"
        relevance_level = "noise"
        sentence_type = "parsing_noise"
        rationale = "Sentence appears too short, section-like, or non-mechanistic."
    elif has_ethanol and has_mechanism and has_pathway:
        ai_relevant = "yes"
        relevance_level = "high"
        sentence_type = "mechanism"
        rationale = "Context links ethanol, mechanism terms, and pathway/intermediate terms."
    elif has_evidence and (has_ethanol or has_oxygenate or has_pathway or has_mechanism):
        ai_relevant = "yes"
        relevance_level = "medium"
        sentence_type = "evidence"
        rationale = "Context contains mechanism evidence terms such as DFT, spectroscopy, isotope, or energy barriers."
    elif has_mechanism and (has_ethanol or has_oxygenate or has_pathway):
        ai_relevant = "yes"
        relevance_level = "medium"
        sentence_type = "pathway" if has_pathway else "mechanism"
        rationale = "Context contains mechanism wording plus ethanol, oxygenate, or pathway terms."
    elif is_performance:
        ai_relevant = "no"
        relevance_level = "low"
        sentence_type = "product_performance"
        rationale = "Sentence mainly describes product performance rather than formation mechanism."
    else:
        ai_relevant = "uncertain"
        relevance_level = "low"
        sentence_type = "background"
        rationale = "Keyword match is present, but mechanism relevance is not explicit."

    needs_context = "yes" if row.get("previous_sentence") or row.get("next_sentence") else "no"
    ethanol_specific = "yes" if has_ethanol else "uncertain"
    oxygenate_related = "yes" if has_oxygenate else "no"

    return {
        "ai_relevant": ai_relevant,
        "relevance_level": relevance_level,
        "sentence_type": sentence_type,
        "ethanol_specific": ethanol_specific,
        "oxygenate_related": oxygenate_related,
        "needs_context": needs_context,
        "semantic_score": semantic_score,
        "ai_filter_rationale": rationale,
    }


def write_quality_report(labeled_all: pd.DataFrame, candidates: pd.DataFrame) -> None:
    conversion_log = pd.read_excel(CONVERSION_LOG_PATH) if CONVERSION_LOG_PATH.exists() else pd.DataFrame()
    total_pdfs = len(conversion_log) if not conversion_log.empty else ""
    converted_txt_files = int(conversion_log["status"].isin(["converted", "exists"]).sum()) if not conversion_log.empty else ""
    failed_pdfs = int((conversion_log["status"] == "failed").sum()) if not conversion_log.empty else ""

    report = pd.DataFrame(
        [
            {
                "total_pdfs": total_pdfs,
                "converted_txt_files": converted_txt_files,
                "failed_pdfs": failed_pdfs,
                "total_candidate_sentences": len(labeled_all),
                "ai_relevant_sentences": int((labeled_all["ai_relevant"] == "yes").sum()),
                "filtered_candidate_sentences": len(candidates),
                "high_relevance_sentences": int((labeled_all["relevance_level"] == "high").sum()),
                "medium_relevance_sentences": int((labeled_all["relevance_level"] == "medium").sum()),
                "evidence_sentences": int((labeled_all["sentence_type"] == "evidence").sum()),
                "noise_sentences": int((labeled_all["relevance_level"] == "noise").sum()),
                "avg_sentences_per_paper": round(len(labeled_all) / max(labeled_all["paper_id"].nunique(), 1), 2),
            }
        ]
    )
    report.to_excel(QUALITY_REPORT_PATH, index=False)


def main() -> None:
    df = pd.read_excel(INPUT_PATH)
    labels = pd.DataFrame([classify_row(row) for _, row in df.iterrows()])
    out = pd.concat([df, labels], axis=1)
    relevance_order = {"high": 0, "medium": 1, "low": 2, "noise": 3}
    out["_relevance_rank"] = out["relevance_level"].map(relevance_order).fillna(9)
    out.sort_values(["_relevance_rank", "semantic_score"], ascending=[True, False], inplace=True)
    out.drop(columns=["_relevance_rank"], inplace=True)
    candidates = out[
        (out["ai_relevant"] == "yes") & (out["relevance_level"].isin(["high", "medium"]))
    ].copy()

    LABELED_ALL_PATH.parent.mkdir(exist_ok=True)
    out.to_excel(LABELED_ALL_PATH, index=False)
    candidates.to_excel(CANDIDATES_PATH, index=False)
    write_quality_report(out, candidates)
    print(f"AI-oriented labeled all -> {LABELED_ALL_PATH.relative_to(ROOT)}")
    print(f"AI-oriented mechanism candidates -> {CANDIDATES_PATH.relative_to(ROOT)}")
    print(f"Extraction quality report -> {QUALITY_REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
