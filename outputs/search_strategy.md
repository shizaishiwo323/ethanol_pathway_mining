# CO2/CO 电还原生成乙醇路径文献检索策略

检索日期：2026-05-23

## 1. 本轮目标

按照 `计划.md` 的阶段 2，先建立一版可追踪、可复核的文献清单。用户额外限定：检索范围为影响因子大于 10 的期刊。

本轮只做“候选文献清单”，不把自动检索结果直接当成路径归类结论。`mentioned_pathways`、`main_pathway`、`pathway_sentence` 需要后续阅读全文或至少摘要/图注后再确认。

## 2. 时间和主题范围

- 年份：2020-2026
- 反应：CO2 electroreduction / CO2RR；CO electroreduction / CORR
- 目标产物：ethanol / C2H5OH；同时保留少量“ethanol and ethylene selectivity branching”相关机制文献
- 主题：pathway / mechanism / intermediate / C-C coupling / dimerization / operando / DFT

## 3. 检索式

主检索式：

```text
("ethanol" OR "C2H5OH" OR "C2+ oxygenates" OR "alcohol")
AND
("pathway" OR "mechanism" OR "C-C coupling" OR "C–C coupling" OR "dimerization" OR "intermediate")
AND
("CO2 reduction" OR "CO2RR" OR "CO electroreduction" OR "CORR" OR "electrochemical CO2 reduction")
```

补充分支：

```text
("ethanol" OR "C2H5OH")
AND
("CO2 electroreduction" OR "CO2 reduction reaction" OR "CO2RR")
AND
("mechanism" OR "pathway" OR "C-C coupling" OR "intermediate")
```

```text
("ethanol" OR "C2H5OH")
AND
("CO electroreduction" OR "CO reduction reaction" OR "CORR")
AND
("mechanism" OR "pathway" OR "C-C coupling" OR "intermediate")
```

执行时还使用了以下开放元数据查询短语组合：

- ethanol CO2 electroreduction mechanism C-C coupling intermediate
- ethanol CO2 reduction reaction pathway intermediate C-C coupling
- CO2RR ethanol mechanism pathway intermediate
- CO2 electroreduction ethanol OCCO CO-CHO COH
- CO electroreduction ethanol mechanism pathway C-C coupling
- CORR ethanol mechanism pathway C-C coupling
- electrosynthesis ethanol CO CHx cross-coupling copper
- selective electrosynthesis ethanol asymmetric C-C coupling tandem CO2 reduction
- tin tandem electrocatalyst CO2 reduction ethanol mechanism
- switching CO2 electroreduction ethanol bond cleavage mechanism

## 4. 数据源

- OpenAlex Works API：用于拉取题名、DOI、年份、期刊、作者和摘要元数据。
- Crossref/OpenAlex DOI 元数据：用于 DOI 和期刊信息交叉核对。
- 期刊官网或公开期刊指标页：用于判断期刊是否满足 JIF > 10。

## 5. 影响因子筛选口径

优先采用 2024 Journal Impact Factor / 2-year Impact Factor。部分出版社页面会显示 “2025 released metrics”，其含义通常是 2025 发布的 2024 JCR 年度数据。若期刊官网页面为动态展示或未直接暴露数值，本轮先使用公开期刊指标页作为临时核验，后续建议用学校 Web of Science JCR 导出表替换。

本轮用于筛选的期刊包括：

| journal | public JIF used | note |
| --- | ---: | --- |
| Nature Catalysis | 44.6 | Nature journal metrics, 2024 |
| Nature Energy | 46.7 | public journal metrics, 2024/latest |
| Nature Communications | 15.7 | Nature journal homepage, 2024 |
| Journal of the American Chemical Society | 15.6 | public JCR listing, 2024 |
| ACS Catalysis | 13.1 | ACS Publications metrics, 2024/latest released |
| Advanced Materials | 26.8 | public JCR listing, 2023/2024-adjacent; still >10 |
| Angewandte Chemie International Edition | 16.1 | public JCR listing, 2024/latest |
| Chemical Engineering Journal | 13.2 | public JCR listing, 2024 |
| Nano Research | 10.9 | public JCR listing, 2024/latest |
| Nature Synthesis | 33.0 | public journal metrics, 2024/latest |
| Science Advances | 12.5 | public JCR listing, 2024/latest |
| CCS Chemistry | 11.2 | public JCR listing, 2024/latest |

## 6. 排除规则

本轮从候选结果中排除了：

- ethanol oxidation reaction，而不是 CO2/CO 还原；
- photocatalytic CO2-to-ethanol，而不是电化学还原；
- 只讨论甲烷、甲酸、乙酸、乙二醇或 C3+，且题名/摘要无法支持乙醇路径分析的文章；
- 低影响因子期刊，或本轮无法确认 JIF > 10 的期刊。

## 7. 当前产出

- `outputs/literature_metadata_initial.csv`：第一版候选文献清单。

## 8. 后续建议

1. 用 Web of Science / Scopus 在同一检索式下导出完整记录，替换或补强 OpenAlex 元数据。
2. 用机构 JCR 表统一核验 `journal_if`。
3. 对 CSV 中 `search_relevance = high` 的文章优先下载摘要、正文和图注，提取 `pathway_sentence`。
4. 人工复核 `pathway_hint` 后再填 `mentioned_pathways` 和 `main_pathway`。

## 9. 第二轮补充检索

检索日期：2026-05-23

第二轮检索要求：与第一批 `outputs/literature_metadata_initial.csv` 不重复。执行时先读取第一批 DOI 作为排除集合，再用更宽的机制和选择性关键词检索。

补充检索重点：

- ethanol Faradaic efficiency
- C2H5OH electrosynthesis
- C2+ oxygenates / multicarbon alcohols
- Cu catalyst / oxide-derived Cu / Cu2O / CuAg / Pd-Cu
- operando spectroscopy / in situ Raman / in situ FTIR / XAS
- catalyst-electrolyte microenvironment
- oxygenate/hydrocarbon selectivity
- CO electroreduction under high pressure

第二轮新增产出：

- `outputs/literature_metadata_batch2.csv`

第二轮保留规则：

- DOI 必须不在第一批中；
- 期刊 `journal_if > 10`；
- 题名或摘要需要能支持 CO2RR/CORR、乙醇/多碳醇/氧化物分支、C-C 偶联或机制分析之一；
- 对“不是乙醇主产物但有路径参考价值”的记录标为 `included_secondary`。
