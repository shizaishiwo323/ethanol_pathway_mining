# Method Description

## 1. Literature Collection

The current stage uses locally available PDF files. PDFs should be stored in `01_pdfs/`; when that folder is empty, the scripts read the existing `paper_pdf_folder/` directory.

## 2. Pathway Coding System

Ethanol formation pathway statements are normalized into P1-P6:

| pathway_code | pathway_name |
| --- | --- |
| P1 | *CO dimerization pathway |
| P2 | CO-CHO coupling pathway |
| P3 | CO-COH coupling pathway |
| P4 | CO-CHx coupling pathway |
| P5 | OCHO/formate pathway |
| P6 | mixed/unclear pathway |

The detailed rules are stored in `02_metadata/pathway_annotation_rules.md`, and keyword candidates are stored in `02_metadata/pathway_keywords.json`.

## 3. Text Extraction

`scripts/01_pdf_to_text.py` extracts page-marked plain text from each local PDF and writes one `.txt` file per PDF to `03_text/`.

## 4. Mechanism Sentence Extraction

`scripts/02_extract_mechanism_sentences.py` searches extracted text for mechanism-related trigger terms, keeps the page number, and writes candidate evidence sentences to `04_extract_results/extracted_mechanism_sentences.xlsx`.

## 5. Automatic Pathway Matching

`scripts/03_match_pathways.py` applies the P1-P6 keyword dictionary to candidate sentences and writes `04_extract_results/auto_pathway_matches.xlsx`. These labels are candidates only and require manual review.

## 6. Manual Review And Statistics

Manual review is performed in `05_manual_check/manual_check.xlsx`. After review, `scripts/04_summarize_by_paper.py`, `scripts/05_statistics.py`, `scripts/06_plot_bar.py`, and `scripts/07_plot_sankey.py` produce paper-level summaries, frequency tables, and figures.
