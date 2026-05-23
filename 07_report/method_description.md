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

`scripts/02_extract_mechanism_sentences.py` searches extracted text for mechanism-related trigger terms, keeps the page number, previous sentence, candidate sentence, next sentence, trigger categories, and keyword score. It writes raw and deduplicated outputs to `04_extract_results/`.

## 5. AI-Oriented Semantic Pre-Filtering

`scripts/02b_ai_filter_mechanism_sentences.py` applies an AI-oriented rule-based pre-filtering rubric aligned with `02_metadata/ai_sentence_filter_prompt.md`. It writes all labeled sentences to `04_extract_results/ai_mechanism_sentence_labeled_all.xlsx` and the high/medium mechanism candidates to `04_extract_results/ai_mechanism_sentence_candidates.xlsx`.

## 6. Pathway Matching And Statistics

Downstream P1-P6 matching and statistics can be run after the semantic pre-filtering stage. Automatic labels remain candidate labels unless they are verified by a stronger review process.
