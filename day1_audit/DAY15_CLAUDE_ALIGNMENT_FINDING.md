# Day 15 finding — Claude Sonnet 4 ArenaHard alignment

## Result

The Day 14 strict comparison reports 12/13 model matches because one Claude Sonnet 4 prompt differs only in whitespace immediately before a colon.

- Partition version: `...dummy inputs : image_points = ...`
- Aggregate version: `...dummy inputs :image_points = ...`
- Both records have score `0`.
- The Day 15 audit reports zero shared-prompt score-multiplicity differences.
- Both sides contain 750 records and 750 unique prompt strings.

## Interpretation

This is a punctuation-spacing discrepancy, not evidence of different prompt coverage or a different recorded score for the affected item. The strict normalizer collapses whitespace runs but does not canonicalize whitespace adjacent to punctuation, so it correctly preserves the textual difference and consequently reports a multiset mismatch.

For alignment diagnostics only, a narrowly scoped canonicalization that removes whitespace immediately before a colon would make these two prompt strings equal. This canonicalization must not be applied to the actual model inputs, feature extraction, or score data.

## Experimental handling

- Retain Claude Sonnet 4 in the 13-model candidate pool.
- Preserve the original archive and original prompt text.
- Keep the strict Day 14 result as an audit observation, annotated as formatting-only after the Day 15 inspection.
- If a canonicalized comparison is added, report both strict and canonicalized results and document the exact transformation.
- Do not silently rewrite source records or use target performance to decide whether to retain a candidate.

## Status

The Claude-specific alignment discrepancy is explained to the extent supported by the supplied audit output. The full Avengers-Pro OOD baseline remains unrun; this finding is not a performance result.
