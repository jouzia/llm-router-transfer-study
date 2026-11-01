# Research 3 — Publication and Release Completion Checklist

The audit log shows that a defined pipeline ran successfully; it does not certify the paper, full repository, licensing, or publication readiness.

## A. Freeze experiment state
- [ ] Preserve full audit log and backup path.
- [ ] Save exact Git commit SHA and branch.
- [ ] Record Python version and dependencies in a reproducible lock/requirements file.
- [ ] Hash the exact scripts executed.
- [ ] Investigate the stray untracked path `earch3` before including anything from it.
- [ ] Review all changed/untracked files and run `git diff --check`.
- [ ] Confirm reruns reproduce summary metrics and output schemas.

## B. Scientific correctness
- [ ] Verify method details directly from source scripts/configs: feature definitions, model class, labels, split logic, candidate pool, score conventions.
- [ ] Confirm Day 4 report and CSV came from the same current script version.
- [ ] Recompute headline means and paired differences from per-prompt CSVs.
- [ ] Recompute confidence intervals and verify bootstrap count, seed, resampling unit, and paired-difference calculation.
- [ ] Validate score comparability across models/targets.
- [ ] Keep Gemini fixed-baseline and source-validation-selected-baseline comparisons separate.
- [ ] Treat repeated seeds over the same target prompts as sensitivity analyses.
- [ ] Exclude cost/latency claims until units and metric semantics are validated.
- [ ] Audit leakage: target scores cannot influence feature design, alpha selection, baseline selection, or seed choice.
- [ ] Document prompt-bootstrap intervals as conditional on observed target prompts.

## C. Related work and novelty
- [ ] Compare exact question/protocol with LLMRouterBench, RouterBench, and RouteLLM.
- [ ] Add a dated literature search protocol and inclusion criteria.
- [ ] State the contribution precisely; if no methodological novelty is defensible, frame as transfer/reproducibility evaluation.
- [ ] Avoid unsupported “first”, “state-of-the-art”, or “beats existing routers” claims.

## D. Reproducible repository
- [ ] README has one clean setup path from a fresh clone.
- [ ] Verify pinned dependency compatibility and a clean installation.
- [ ] Provide commands for each experiment and a documented all-experiments command.
- [ ] List expected outputs and their meanings.
- [ ] Add a machine-readable manifest with commit/script/archive hashes, environment, seeds, split names, candidate pool, and timestamp.
- [ ] Add a result-validation script for schemas, row counts, and tolerance-based headline metrics.
- [ ] Ensure no secrets, private files, local paths, or restricted raw archive data are committed.
- [ ] Validate CSV schemas, duplicate keys, missing values, and row counts.
- [ ] Separate code, reports, figures, and generated results.

## E. Figures and tables
- [ ] Figure 1: source-to-target transfer study design.
- [ ] Figure 2: paired router-minus-Gemini differences with confidence intervals.
- [ ] Figure 3: baseline selection frequencies across source-validation seeds.
- [ ] Table: dataset/model coverage and exclusions.
- [ ] Table: primary results and uncertainty.
- [ ] Generate figures from saved CSVs; do not hardcode results in plotting code.
- [ ] Captions note that target prompts are reused across validation seeds.

## F. Data provenance and licensing
- [ ] Verify current upstream LICENSE and archive terms.
- [ ] Verify underlying dataset, prompt, ground-truth, model-output, and provider terms.
- [ ] Do not redistribute raw archive/restricted records without clear permission.
- [ ] Cite upstream paper, repository, release, and maintainer clarification.
- [ ] Explain data access under applicable terms.

## G. Submission readiness
- [ ] Cross-check every reported number against raw per-prompt CSVs.
- [ ] Include abstract, introduction, related work, method, data, results, discussion, limitations, data/ethics statement, reproducibility statement, and references.
- [ ] Verify author affiliation only if accurate and desired.
- [ ] Check grammar and citation/reference consistency.
- [ ] Export and inspect PDF pages, tables, equations, and figures.
- [ ] Add verified `CITATION.cff`.
- [ ] Tag a release only after tests and artifact checks pass.

## Current decision gate
**Passed:** the supplied audit's execution/integrity checks.
**Not established:** publication readiness, algorithmic novelty, superiority to strongest fixed baseline, broad generalization, and license clearance.

Do not mark publication-ready until the blocking items above are resolved or explicitly disclosed.
