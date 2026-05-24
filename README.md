# Ethanol Pathway Mining

This project organizes literature mining and visualization for ethanol formation pathways in electrochemical CO2/CO reduction.

## Goal

The goal of the current stage is to convert public PDF papers into text, extract mechanism-related candidate sentences, and use AI-oriented semantic pre-filtering to identify sentences that are likely relevant to ethanol formation mechanisms.

## Project Structure

- `00_project_notes/`: project workflow and working notes.
- `01_pdfs/`: local paper PDFs.
- `02_metadata/`: literature metadata and pathway coding tables.
- `03_text/`: extracted text from PDFs.
- `04_extract_results/`: automatic pathway sentence extraction outputs.
- `05_manual_check/`: downstream pathway-level checking tables retained for later stages.
- `05_statistics/`: paper-level pathway summaries, conflict reports, and frequency tables.
- `06_figures/`: generated figures.
- `07_report/`: final reports and narrative summaries.
- `scripts/`: reusable Python scripts for extraction, cleaning, statistics, and plotting.

## Notes

- Do not overwrite raw data; save cleaned or derived data as separate files.
- Track pathway evidence sentences, page numbers, and sentence context.
- `scripts/02b_ai_filter_mechanism_sentences.py` does not call an external LLM API; it prepares prioritized, rule-based candidate tables for downstream Codex-based semantic analysis.

## Current Workflow

1. Store public PDF papers in `01_pdfs/`, or use the existing fallback folder `paper_pdf_folder/`.
2. Run `python scripts/01_pdf_to_text.py` to convert PDFs into text files stored in `03_text/`.
3. Run `python scripts/02_extract_mechanism_sentences.py` to extract keyword-triggered candidate sentences with previous/next sentence context.
4. Run `python scripts/02b_ai_filter_mechanism_sentences.py` to apply AI-oriented semantic pre-filtering.
5. Check `04_extract_results/ai_mechanism_sentence_labeled_all.xlsx`, `04_extract_results/ai_mechanism_sentence_candidates.xlsx`, and `04_extract_results/extraction_quality_report.xlsx`.
6. Run `python scripts/03_rule_match_pathways.py` to create `04_extract_results/03_rule_pathway_matches.xlsx`.
7. Run `python scripts/04_prepare_ai_pathway_review.py` to create the compact AI review input and batch files.
8. Run `python scripts/04_codex_semantic_pathway_review.py` to generate `04_extract_results/04_ai_pathway_review_results.xlsx`.
9. Run `python scripts/05_summarize_pathways_by_paper.py` to create paper-level pathway and AI summaries.
10. Run `python scripts/06_check_pathway_conflicts.py` to create the conflict report and second-pass resolution template.
11. Run `python scripts/07_calculate_pathway_frequency.py` to create `05_statistics/pathway_frequency_summary.xlsx`.

## Stage 4-6 Outputs

- `04_extract_results/03_rule_pathway_matches.xlsx`: sentence-level P1-P6 keyword matches. These are rule candidates only.
- `04_extract_results/04_ai_pathway_review_input.xlsx`: compact AI review input.
- `04_extract_results/04_ai_pathway_review_results.xlsx`: sentence-level semantic pathway decisions, including role, evidence type, confidence, and statistics inclusion.
- `05_statistics/paper_level_pathway_summary.xlsx`: paper-level aggregation of mentioned, main, compared, rejected, and ethanol-specific pathways.
- `05_statistics/paper_level_ai_summary.xlsx`: paper-level AI summary used for the final frequency table.
- `05_statistics/pathway_conflict_report.xlsx`: cases needing second-pass review, such as multiple main pathways or main/reject conflicts.
- `05_statistics/pathway_conflict_ai_resolved.xlsx`: template for resolved conflict decisions. `scripts/07_calculate_pathway_frequency.py` uses non-empty resolution decisions when present.
- `05_statistics/pathway_frequency_summary.xlsx`: final coarse/fine pathway distribution table by paper count.
