# Research 3 — Day 2 Final Experimental Report

## Status and scope
**Day 2 pilot and documentation stage: complete.** The project itself is not complete, and this report does not establish novelty, statistical significance, or publication readiness.

Working research direction: evaluating whether lightweight prompt features can improve model selection, followed by a stronger investigation of uncertainty-aware routing under domain shift.

## Research question
Can lightweight prompt-level features help select a suitable language model compared with a single global model and a model selected for each known domain?

## Data and integrity
- Local source: LLMRouterBench result archive.
- Archive SHA-256: `b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`.
- Archive audit: 700 JSON files, zero parse errors, 27 datasets and 40 distinct model names across the full archive.
- Pilot domains: ArenaHard Coding (253 prompts), ArenaHard Creative Writing (250), and ArenaHard Math (247).
- Pilot matrix: 750 prompts and 33 common models.
- Feature table: 11 lightweight prompt features; prompt and ground-truth alignment checks passed.
- Scores in the pilot are discrete: 0, 0.5, and 1.

A checksum establishes integrity relative to the recorded digest; it does not establish data provenance, licensing, or scientific validity.

## Methods
Three strategies were compared:
1. Global model selected from training data using an equal-weight macro-average across domains.
2. Domain-aware model selected from training data for each known domain.
3. Ridge-regression feature router predicting model scores from 11 prompt features.

Five train/validation/test splits were evaluated with seeds 42, 43, 44, 45, and 46. Validation was used for hyperparameter selection. The oracle is a test-informed upper bound and is not deployable.

## Structural validation
The saved prediction file contains 760 rows and 760 unique seed-domain-prompt keys. Required strategy columns were present, and scores were finite and within [0,1]. The three domains and five seeds were represented.

## Preliminary results
Using equal-weight domain macro scores calculated from saved predictions:
- Mean feature-router minus domain-aware score difference across the five split results: approximately +0.0171.
- Mean feature-router minus global score difference across the five split results: approximately +0.0317.

These averages are descriptive, not independent replications. The same underlying prompts recur across split seeds. Previously computed paired bootstrap intervals included zero. The feature router did not win in every split. Therefore, a statistically reliable improvement has not been established.

## Archive metric audit
- 700/700 JSON files parsed successfully.
- Two files have aggregate performance values that disagree with the mean of per-record scores.
- Thirty-nine files have aggregate cost values that disagree with the sum of per-record costs.
- Repeated aggregate time and cost values were observed for many models across related ArenaHard datasets.
- The repository aggregator contains logic for summing record costs and token counts and averaging record scores. This does not by itself establish the generation semantics or units of every archived field.
- The pilot uses per-record scores; the two aggregate score discrepancies were flagged. Cost and latency are excluded from comparative claims until their definitions and consistency are verified.

## Licensing and provenance
At audited repository commit `c77cb0506949d8f959e97967d2fefca0e8ff1b05`, the README advertises an MIT license but the tracked root `LICENSE` file is absent. The two tracked license files found belong to individual baselines. This is not sufficient evidence that the entire repository, benchmark datasets, archived outputs, or derived artifacts share one license. Do not redistribute data until rights and provenance are verified.

## Related work and novelty
The related-work matrix records established directions including LLMRouterBench, RouteLLM, RouterBench, FrugalGPT, EmbedLLM, Model-SAT, RACER, LENS, RouterEval, TwinRouterBench, R2-Router, and The Routing Plateau.

Generic LLM routing, model selection, cost-quality trade-offs, routing benchmarks, uncertainty-aware routing, and distribution-shift-aware routing are not new in themselves. The current pilot does not establish a novel contribution. The candidate direction—robust model selection under domain shift with calibrated uncertainty, explicit risk/quality constraints, and fallback or abstention—must be narrowed against the full prior art and tested against strong baselines before it can be claimed as a contribution.

## Limitations
1. Only three related ArenaHard domains were evaluated.
2. Five random splits reuse the same underlying prompts.
3. The bootstrap analysis does not account for all sources of uncertainty, including benchmark provenance and model-selection effects.
4. Lexical and structural features may not represent prompt semantics or true task difficulty.
5. Archived cost/time fields need semantic and aggregation verification.
6. Licensing and data provenance are unresolved.
7. Generalization to an unseen benchmark family has not been tested.
8. No novelty or publication-readiness claim is warranted.

## Next research phase
1. Complete full-paper prior-art comparison with exact method, dataset, baselines, metrics, shift setup, and limitations.
2. Verify source-level data provenance, licenses, and archived metric units.
3. Predefine a leakage-resistant evaluation using an unseen benchmark family or domain.
4. Compare with strong published routing baselines and simple non-neural baselines.
5. Report paired uncertainty with explicit dependence caveats.
6. Evaluate cost/latency only after validating measurement definitions.
7. Preserve scripts, environment versions, split manifests, checksums, and generated reports.

## Conclusion
Day 2's pilot, structural validation, archive metric audit, preliminary related-work map, and documentation are complete. Results suggest that lightweight prompt features may contain useful routing signal, but the gain is inconsistent and not statistically established. The project must proceed with stronger generalization testing and prior-art validation before any novelty or publication claim.
