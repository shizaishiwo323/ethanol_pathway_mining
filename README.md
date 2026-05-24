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
