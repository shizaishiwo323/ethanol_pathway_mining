# AI Sentence Filter Prompt

You are screening sentences from electrochemical CO2/CO reduction papers.

Decide whether the candidate sentence is truly relevant to ethanol formation mechanisms, not merely a product-performance sentence or broad background statement.

Use the previous sentence, candidate sentence, and next sentence together.

Return structured labels:

| field | allowed values |
| --- | --- |
| ai_relevant | yes / no / uncertain |
| relevance_level | high / medium / low / noise |
| sentence_type | mechanism / pathway / intermediate / product_performance / background / parsing_noise |
| ethanol_specific | yes / no / uncertain |
| needs_context | yes / no |
| rationale | short reason |

High relevance means the sentence or its immediate context links ethanol formation to a mechanism, pathway, C-C coupling step, intermediate, or pathway comparison.

Medium relevance means the sentence is probably useful but needs nearby context.

Low relevance means the sentence mentions related keywords but mainly discusses catalyst performance, broad C2+ products, or non-ethanol chemistry.

Noise means the sentence is PDF parsing noise, references, figure text fragments, or does not contain interpretable mechanism content.
