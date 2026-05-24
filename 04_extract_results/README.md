# Extraction Outputs

This directory stores reproducible outputs from the PDF-to-text and candidate sentence preparation stage.

## `pdf_conversion_log.xlsx`

PDF conversion log with one row per input PDF. It records source path, output text filename, conversion status, page count, character count, and errors.

## `extracted_mechanism_sentences_raw.xlsx`

Keyword-triggered candidate sentences extracted from PDF-derived text before de-duplication.

## `extracted_mechanism_sentences.xlsx`

Deduplicated candidate sentences with page number, previous sentence, next sentence, trigger terms, trigger categories, and keyword score.

## `ai_mechanism_sentence_labeled_all.xlsx`

All extracted sentences with rule-based, AI-oriented semantic pre-filter labels. Use this as the full audit table. The `sentence_type` field can include `mechanism`, `pathway`, `evidence`, `product_performance`, `background`, or `parsing_noise`.

## `ai_mechanism_sentence_candidates.xlsx`

Filtered high/medium relevance candidate sentences for downstream Codex semantic analysis.

## `extraction_quality_report.xlsx`

One-row quality summary covering PDF conversion, candidate extraction, and semantic pre-filtering.

## `auto_pathway_matches.xlsx`

Keyword-based P1-P6 pathway matches retained for later stages. These are candidate labels only, not final mechanism conclusions.
