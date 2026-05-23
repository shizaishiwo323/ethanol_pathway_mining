# Workflow

This workflow implements the local PDF processing stage.

1. Put local PDFs in `01_pdfs/`. If that folder is empty, scripts fall back to the existing `paper_pdf_folder/`.
2. Build pathway metadata in `02_metadata/`.
3. Convert PDFs to page-marked text files in `03_text/`.
4. Extract mechanism-related sentences into `04_extract_results/extracted_mechanism_sentences.xlsx`.
5. Match P1-P6 pathway keywords into `04_extract_results/auto_pathway_matches.xlsx`.
6. Copy the auto-match table to `05_manual_check/manual_check.xlsx` and manually fill `manual_pathway`, `role`, `ethanol_specific`, `confidence`, and `notes`.
7. Summarize checked annotations by paper and generate pathway frequency figures.

The scripts preserve evidence sentences and do not overwrite raw PDFs.
