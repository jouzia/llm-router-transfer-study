# Proposed Follow-up Protocol (Not Yet Run or Preregistered)

## Objective
Test whether a lightweight prompt-feature router trained on ArenaHard coding, creative-writing, and mathematics records transfers to target benchmarks under a source-only selection protocol.

## Primary endpoint
Mean target score difference: router minus fixed Gemini 2.5 Pro, computed on the same target prompts.

## Secondary endpoint
Router minus source-validation-selected fixed model. Report separately; choose this model using source validation only.

## Data and split policy
- Source data: 750 audited prompts across three ArenaHard domains, 33 models, and 11 extracted features as currently reported.
- Target data: GPQA and MMLU-Pro as currently specified.
- Target labels/scores/outcomes must not influence feature engineering, hyperparameter selection, candidate-pool selection, baseline selection, or seed choice.
- Existing ten-seed runs reuse target prompts; report them only as source-validation sensitivity analyses.
- Define any additional benchmark split, filtering, model intersection, and evaluation rule before inspecting results.

## Statistical analysis
- Use paired per-prompt differences.
- Report mean difference in percentage points and paired bootstrap percentile interval.
- Predefine bootstrap replicate count, seed, and resampling unit.
- Report win/tie/loss counts descriptively.
- Do not treat repeated seeds on the same target set as independent samples.
- State multiplicity handling if multiple targets are confirmatory endpoints.
- Report raw scores and differences; statistical significance alone does not imply practical importance.

## Baselines
1. Fixed Gemini 2.5 Pro reference.
2. Source-validation-selected fixed model.
3. Optional simple heuristic/random baseline if specified before target evaluation.
4. Optional oracle only as a non-deployable upper-bound diagnostic.

## Reporting
Report all target results, including unfavorable ones. Do not select a seed or benchmark after observing results. Disclose that prompt-bootstrap intervals condition on the observed target set.

Any deviation must be listed in the paper. This is a proposal and must not be described as preregistered or completed unless frozen before the corresponding experiment.
