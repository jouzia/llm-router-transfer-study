# Research 3 — Day 2 Reproducibility Checklist

## Verified in the local audit
- [x] Archive contains 700 JSON result files.
- [x] All 700 JSON files parsed without errors.
- [x] Archive SHA-256: b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1
- [x] Pilot matrix contains 750 prompts across 3 ArenaHard domains and 33 models.
- [x] Feature extraction produced 750 prompt rows with no prompt/ground-truth alignment mismatches.
- [x] Five split seeds were evaluated: 42, 43, 44, 45, 46.
- [x] Saved predictions passed structural validation: 760 rows and 760 unique seed-domain-prompt keys.
- [x] Paired analysis was run; previously computed confidence intervals included zero.
- [x] Day 2 final report and archive metric summary exist.

## Data-quality caveats
- [x] Two aggregate performance fields disagree with means of per-record scores.
- [x] Thirty-nine aggregate cost fields disagree with sums of per-record costs.
- [x] Repeated aggregate time/cost values across related ArenaHard datasets were observed.
- [x] Cost and latency are excluded from the pilot's comparative conclusions.
- [x] Root repository LICENSE is absent at the audited commit despite README badge.
- [x] Dataset and output licensing/provenance are unresolved; do not redistribute the archive without verification.

## Statistical caveats
- [x] The five random splits reuse the same underlying benchmark; they are not independent studies.
- [x] The feature-router gain is descriptive and not established as statistically significant.
- [x] The oracle is a test-informed upper bound, not a deployable baseline.
- [x] The pilot only covers three related ArenaHard domains.
- [x] Generalization to unrelated benchmarks and unseen domains has not been tested.

## Prior-art caveats
- [x] Generic LLM routing, model selection, quality-cost trade-offs, and routing benchmarks predate this project.
- [x] Uncertainty-aware and distribution-shift-aware routing are already explored in prior work.
- [x] The candidate contribution is provisional; novelty is not established.
- [ ] Complete full-paper review and citation-level comparison for every directly relevant work.
- [ ] Verify benchmark data terms, source dataset licenses, and provenance.
- [ ] Verify archived cost/time units and aggregation semantics from the collection/evaluation pipeline.
- [ ] Design and preregister a leakage-resistant evaluation on a held-out benchmark family or unseen domain.
- [ ] Compare against stronger published baselines before making superiority claims.

## Day 2 disposition
The pilot, structural checks, archive metric audit, preliminary related-work map, and documentation are complete. Research validity and publication readiness are not established. The unresolved items above are follow-up research tasks, not findings to be silently assumed.
