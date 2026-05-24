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

## `03_rule_pathway_matches.xlsx`

Stage 4 rule-based P1-P6 pathway matches for every row in `ai_mechanism_sentence_candidates.xlsx`. Matching is performed on the candidate sentence itself to reduce context-driven false positives. The output includes `matched_keywords`, `rule_matched_pathways`, `rule_match_count`, and `needs_ai_review`.

## `04_ai_pathway_review_input.xlsx`

Compact table for semantic pathway review. It keeps only the fields needed for AI judgment: paper ID, source text name, sentence ID, sentence, rule-matched pathways, matched keywords, and ethanol/oxygenate flags.

## `04_ai_pathway_review_results.xlsx`

Sentence-level semantic pathway review output. It distinguishes `mention`, `main`, `compare`, `reject`, and `unclear`, and records `ai_final_pathway`, `ai_ethanol_specific`, `ai_evidence_type`, `ai_evidence_reason`, `ai_confidence`, and `ai_include_in_statistics`.

## `ai_review_batches/`

Batch files generated from `04_ai_pathway_review_input.xlsx` for optional external or manual high-intelligence AI review. The current batch size is 150 rows.
