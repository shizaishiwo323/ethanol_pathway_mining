# Workflow

This workflow implements the local PDF processing stage.

1. Put public PDFs in `01_pdfs/`. If that folder is empty, scripts fall back to the existing `paper_pdf_folder/`.
2. Convert PDFs to page-marked text files in `03_text/` and write `04_extract_results/pdf_conversion_log.xlsx`.
3. Extract mechanism-related sentences with previous/next sentence context into `04_extract_results/extracted_mechanism_sentences.xlsx`.
4. Apply AI-oriented semantic pre-filtering with `scripts/02b_ai_filter_mechanism_sentences.py`.
5. Check `04_extract_results/ai_mechanism_sentence_labeled_all.xlsx`, `04_extract_results/ai_mechanism_sentence_candidates.xlsx`, and `04_extract_results/extraction_quality_report.xlsx`.
6. Use the filtered candidates as the evidence pool for later P1-P6 pathway coding.

The scripts preserve evidence sentences and do not overwrite raw PDFs.
