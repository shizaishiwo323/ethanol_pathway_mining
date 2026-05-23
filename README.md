# Ethanol Pathway Mining

This project organizes literature mining and visualization for ethanol formation pathways in electrochemical CO2/CO reduction.

## Project Structure

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
