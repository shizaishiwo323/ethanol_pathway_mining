# Ethanol Pathway Mining

This project organizes literature mining and visualization for ethanol formation pathways in electrochemical CO2/CO reduction.

## Goal

The goal is to extract pathway-related statements from local PDF papers, classify them into P1-P6 ethanol formation pathways, manually verify pathway roles, and visualize pathway frequency distributions.

## Project Structure

- `00_project_notes/`: project workflow and working notes.
- `01_pdfs/`: local paper PDFs.
- `02_metadata/`: literature metadata and pathway coding tables.
- `03_text/`: extracted text from PDFs.
- `04_extract_results/`: automatic pathway sentence extraction outputs.
- `05_manual_check/`: manual review tables.
- `06_figures/`: generated figures.
- `07_report/`: final reports and narrative summaries.
- `scripts/`: reusable Python scripts for extraction, cleaning, statistics, and plotting.

## Notes

- Keep original PDFs local unless redistribution is permitted.
- Do not overwrite raw data; save cleaned or derived data as separate files.
- Track pathway evidence sentences and distinguish `mentioned_pathways` from `main_pathway`.

## Current Workflow

1. Put local PDFs in `01_pdfs/`, or use the existing fallback folder `paper_pdf_folder/`.
2. Run `python scripts/01_pdf_to_text.py`.
3. Run `python scripts/02_extract_mechanism_sentences.py`.
4. Run `python scripts/03_match_pathways.py`.
5. Review `05_manual_check/manual_check.xlsx` manually.
6. After review, run scripts `04_summarize_by_paper.py` through `07_plot_sankey.py`.
