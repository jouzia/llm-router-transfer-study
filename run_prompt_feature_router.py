
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path((Path(__file__).resolve().parent / "day1_audit"))
INPUT = ROOT / "prompt_feature_score_table.csv"
PREDICTIONS_OUT = ROOT / "prompt_router_test_predictions.csv"
SUMMARY_OUT = ROOT / "prompt_router_experiment_summary.txt"

SEEDS = [42, 43, 44, 45, 46]
ALPHAS = [0.1, 1.0, 10.0, 100.0]

META_COLUMNS = {"dataset", "index", "prompt_text_source"}
FEATURE_COLUMNS = [
    "char_count",
    "word_count",
    "line_count",
    "digit_count",
    "question_mark_count",
    "exclamation_count",
    "code_symbol_count",
    "contains_code_fence",
    "contains_url",
    "contains_equation_symbol",
    "contains_question_word",
]


def mean(values):
    return statistics.mean(values) if values else float("nan")


def fit_predictor(X_train, y_train, X_eval, alpha):
    model = make_pipeline(
        StandardScaler(),
        Ridge(alpha=alpha),
    )
    model.fit(X_train, y_train)
    return model.predict(X_eval)


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(f"Missing input file: {INPUT}")

    with INPUT.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise ValueError("Input table is empty.")

    columns = list(rows[0])
    missing_features = [c for c in FEATURE_COLUMNS if c not in columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")

    models = [c for c in columns if c not in META_COLUMNS
              and c not in FEATURE_COLUMNS]

    if not models:
        raise ValueError("No model-score columns found.")

    domains = sorted({r["dataset"] for r in rows})

    # Convert all numeric fields once. Each row is one prompt,
    # with every model's score stored alongside that prompt.
    X_by_domain = {}
    Y_by_domain = {}
    row_by_domain = {}

    for domain in domains:
        domain_rows = sorted(
            [r for r in rows if r["dataset"] == domain],
            key=lambda r: int(r["index"]),
        )

        X_by_domain[domain] = np.asarray([
            [float(r[c]) for c in FEATURE_COLUMNS]
            for r in domain_rows
        ], dtype=float)

        Y_by_domain[domain] = np.asarray([
            [float(r[m]) for m in models]
            for r in domain_rows
        ], dtype=float)

        row_by_domain[domain] = domain_rows

        if not np.isfinite(X_by_domain[domain]).all():
            raise ValueError(f"Non-finite features in {domain}")
        if not np.isfinite(Y_by_domain[domain]).all():
            raise ValueError(f"Non-finite scores in {domain}")

    all_prediction_rows = []
    summary_lines = [
        "RESEARCH 3 — PROMPT-FEATURE ROUTING EXPERIMENT",
        "=" * 65,
        f"Input: {INPUT}",
        f"Domains: {len(domains)}",
        f"Prompts: {len(rows)}",
        f"Candidate models: {len(models)}",
        f"Features: {len(FEATURE_COLUMNS)}",
        f"Seeds: {SEEDS}",
        f"Ridge alpha candidates: {ALPHAS}",
        "",
        "Protocol: per-domain random prompt split; 60% train, 20% "
        "validation, 20% test.",
        "Alpha selected using validation only. Final models and "
        "baseline policies use train+validation.",
        "All policies are evaluated on identical test prompts.",
        "Oracle is test-informed and is only an upper bound.",
        "",
    ]

    for seed in SEEDS:
        rng = np.random.default_rng(seed)
        splits = {}

        # Split prompts, not model-score cells, preventing the same
        # prompt from appearing in both training and test sets.
        for domain in domains:
            n = len(row_by_domain[domain])
            indices = rng.permutation(n)

            n_train = int(n * 0.60)
            n_val = int(n * 0.20)

            train_idx = indices[:n_train]
            val_idx = indices[n_train:n_train + n_val]
            test_idx = indices[n_train + n_val:]

            splits[domain] = (train_idx, val_idx, test_idx)

        # Tune one shared regularization strength on validation data.
        validation_scores = {}

        for alpha in ALPHAS:
            domain_scores = []

            for domain in domains:
                X = X_by_domain[domain]
                Y = Y_by_domain[domain]
                train_idx, val_idx, _ = splits[domain]

                predictions = np.column_stack([
                    fit_predictor(
                        X[train_idx],
                        Y[train_idx, j],
                        X[val_idx],
                        alpha,
                    )
                    for j in range(len(models))
                ])

                chosen = np.argmax(predictions, axis=1)
                actual = Y[val_idx, chosen]
                domain_scores.append(float(np.mean(actual)))

            validation_scores[alpha] = float(np.mean(domain_scores))

        # Deterministic tie-break: choose the larger alpha if validation
        # means are exactly equal, favoring stronger regularization.
        chosen_alpha = max(
            ALPHAS,
            key=lambda a: (validation_scores[a], a),
        )

        # Select global and domain-specific models using train+validation.
        fit_indices = {}
        for domain in domains:
            train_idx, val_idx, test_idx = splits[domain]
            fit_indices[domain] = np.concatenate([train_idx, val_idx])

        # Select one global model by equal-weight macro-average
        # training performance across domains.
        global_domain_means = np.stack([
            Y_by_domain[d][fit_indices[d]].mean(axis=0)
            for d in domains
        ], axis=0)

        global_means = global_domain_means.mean(axis=0)
        global_model_index = int(np.argmax(global_means))
        global_model = models[global_model_index]

        domain_model_indices = {}
        for domain in domains:
            domain_model_indices[domain] = int(
                Y_by_domain[domain][fit_indices[domain]]
                .mean(axis=0)
                .argmax()
            )

        seed_strategy_scores = defaultdict(list)
        seed_domain_scores = defaultdict(lambda: defaultdict(list))

        for domain in domains:
            X = X_by_domain[domain]
            Y = Y_by_domain[domain]
            fit_idx = fit_indices[domain]
            _, _, test_idx = splits[domain]

            X_fit = X[fit_idx]
            X_test = X[test_idx]
            Y_fit = Y[fit_idx]
            Y_test = Y[test_idx]

            # Predict every candidate model's expected score.
            predicted = np.column_stack([
                fit_predictor(
                    X_fit,
                    Y_fit[:, j],
                    X_test,
                    chosen_alpha,
                )
                for j in range(len(models))
            ])

            feature_choices = np.argmax(predicted, axis=1)
            global_scores = Y_test[:, global_model_index]
            domain_scores = Y_test[:, domain_model_indices[domain]]
            feature_scores = Y_test[
                np.arange(len(test_idx)), feature_choices
            ]
            oracle_scores = Y_test.max(axis=1)

            strategies = {
                "global": global_scores,
                "domain_aware": domain_scores,
                "prompt_feature_ridge": feature_scores,
                "oracle_upper_bound": oracle_scores,
            }

            for strategy, values in strategies.items():
                seed_strategy_scores[strategy].extend(
                    values.astype(float).tolist()
                )
                seed_domain_scores[strategy][domain].extend(
                    values.astype(float).tolist()
                )

            for local_pos, original_idx in enumerate(test_idx):
                chosen_idx = int(feature_choices[local_pos])
                record = row_by_domain[domain][int(original_idx)]

                all_prediction_rows.append({
                    "seed": seed,
                    "domain": domain,
                    "prompt_index": record["index"],
                    "selected_alpha": chosen_alpha,
                    "global_model": global_model,
                    "domain_model": models[domain_model_indices[domain]],
                    "feature_selected_model": models[chosen_idx],
                    "global_test_score": float(
                        global_scores[local_pos]
                    ),
                    "domain_aware_test_score": float(
                        domain_scores[local_pos]
                    ),
                    "feature_router_test_score": float(
                        feature_scores[local_pos]
                    ),
                    "oracle_test_score": float(
                        oracle_scores[local_pos]
                    ),
                })

        summary_lines.append(
            f"SEED {seed} | selected alpha={chosen_alpha} | "
            f"validation scores={validation_scores}"
        )

        for strategy in (
            "global",
            "domain_aware",
            "prompt_feature_ridge",
            "oracle_upper_bound",
        ):
            score = mean(seed_strategy_scores[strategy])
            summary_lines.append(
                f"  {strategy}: pooled test mean={score:.6f}"
            )

        feature_mean = mean(
            seed_strategy_scores["prompt_feature_ridge"]
        )
        domain_mean = mean(seed_strategy_scores["domain_aware"])
        global_mean = mean(seed_strategy_scores["global"])
        oracle_mean = mean(seed_strategy_scores["oracle_upper_bound"])

        summary_lines.append(
            f"  feature minus domain-aware: "
            f"{feature_mean - domain_mean:+.6f}"
        )
        summary_lines.append(
            f"  feature minus global: {feature_mean - global_mean:+.6f}"
        )
        summary_lines.append(
            f"  oracle minus feature: {oracle_mean - feature_mean:+.6f}"
        )

        for domain in domains:
            summary_lines.append(f"  DOMAIN {domain}")
            for strategy in (
                "global",
                "domain_aware",
                "prompt_feature_ridge",
                "oracle_upper_bound",
            ):
                summary_lines.append(
                    f"    {strategy}: "
                    f"{mean(seed_domain_scores[strategy][domain]):.6f}"
                )
        summary_lines.append("")

    # Write prompt-level predictions for paired analysis.
    if all_prediction_rows:
        with PREDICTIONS_OUT.open(
            "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.DictWriter(
                f, fieldnames=list(all_prediction_rows[0])
            )
            writer.writeheader()
            writer.writerows(all_prediction_rows)

    summary_lines.extend([
        "INTERPRETATION NOTES",
        "-" * 65,
        "1. These are benchmark-specific held-out results, not proof of",
        "   generalization to unseen domains or new benchmark families.",
        "2. Five seeds provide split-sensitivity checks; they are not five",
        "   independent studies.",
        "3. The oracle sees test outcomes and is not deployable.",
        "4. No statistical-significance claim is made by this script.",
        "5. Prompt features are intentionally simple and interpretable.",
        "",
        f"Predictions CSV: {PREDICTIONS_OUT}",
        f"Summary: {SUMMARY_OUT}",
    ])

    SUMMARY_OUT.write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print("\n".join(summary_lines))
    print("\nExperiment complete.")


if __name__ == "__main__":
    main()
