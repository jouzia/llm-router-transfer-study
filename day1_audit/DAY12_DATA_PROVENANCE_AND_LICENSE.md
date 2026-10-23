# Day 12 — Data Provenance and Usage Permissions

**Review date:** 23 October 2026

## 1. Archive provenance and integrity

The study uses the `bench-release.tar.gz` benchmark-results archive associated with the LLMRouterBench project.

Expected SHA-256:

`b79f8cde1a6f029c2efa663a3a3b6f7748defb22341fe59f328cebef6648c8f1`

The local archive hash was checked against this value.

## 2. Maintainer permission

In [LLMRouterBench GitHub issue #5](https://github.com/ynulihao/LLMRouterBench/issues/5), the repository maintainer stated on 26 August 2026 that:

- The MIT license is intended to apply to the top-level repository source code.
- The `bench-release.tar.gz` benchmark data may be used for non-commercial academic research and reproduction of research results.
- The maintainers intended to add license files and update the Hugging Face dataset card to make these terms explicit.

This is written maintainer confirmation of the stated intended use. It is not treated as blanket permission for commercial use or unrestricted redistribution.

## 3. Underlying benchmark terms

The archive contains results associated with multiple benchmark families. Underlying dataset licenses and model-provider terms may impose additional conditions.

The licenses and terms applicable to the exact versions and records used in this study have not all been independently established. The maintainer's permission does not replace that verification.

## 4. Research handling decision

- Continue non-commercial academic analysis and preparation of research reports, consistent with the maintainer's written clarification.
- Cite the LLMRouterBench paper, repository, and maintainer clarification.
- Preserve the archive hash, extraction details, scripts, experiment configurations, and aggregate results for reproducibility.
- Do not redistribute the raw archive or potentially restricted prompt, ground-truth, or model-output records until the relevant terms have been checked.
- Do not claim commercial-use permission.
- Recheck the repository's LICENSE file and Hugging Face dataset-card metadata before public release.

## 5. Outstanding limitation

The maintainer's response was located, but the promised formal license documentation was not confirmed during the checks conducted on 23 October 2026.

**Status:** Written maintainer clarification located; formal documentation and complete third-party terms verification remain outstanding.

## 6. Research interpretation

This licensing review is a provenance and compliance limitation. It does not change the experimental results or establish that the proposed routing method is novel. Claims about routing performance must continue to reflect the observed benchmark results and baseline sensitivity.
