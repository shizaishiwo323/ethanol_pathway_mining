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

Compact table for semantic pathway review. It keeps paper ID, source text name, sentence ID, page, previous sentence, sentence, next sentence, rule-matched pathways, matched keywords, and ethanol/oxygenate flags.

## `04_ai_pathway_review_results.xlsx`

Sentence-level semantic pathway review output. Preferred generation script: `scripts/04b_deepseek_pathway_review.py`. Offline fallback: `scripts/04_rule_based_semantic_pathway_review.py`. It distinguishes `mention`, `main`, `compare`, `reject`, and `unclear`, and records `ai_final_pathway`, `ai_ethanol_specific`, `ai_evidence_type`, `ai_evidence_reason`, `ai_confidence`, and `ai_include_in_statistics`.

When the DeepSeek script is used, `review_source` records whether a row was returned by DeepSeek or retained as `fallback_not_sent`. The fallback rows remain in the audit table but are excluded from final statistics.

## `deepseek_review_raw_jsonl.jsonl`

Raw DeepSeek API responses for sentence-level review. This file is created only when `scripts/04b_deepseek_pathway_review.py` is run.

## `deepseek_review_failed_rows.xlsx`

Rows that failed API calls, JSON parsing, or required-field validation during DeepSeek sentence-level review.

## `ai_review_batches/`

Batch files generated from `04_ai_pathway_review_input.xlsx` for optional external or manual high-intelligence AI review. The current batch size is 150 rows.
