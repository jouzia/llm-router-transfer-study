import ast
import csv
import json
import re
import tarfile
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "day1_audit"
ARCHIVE = ROOT / "bench-release.tar.gz"
META = AUDIT / "all_result_metadata.csv"
SOURCE = AUDIT / "prompt_feature_score_table.csv"
OUT = AUDIT / "DAY9_MATCHED_POOL_GPQA_RESULTS.txt"
DETAIL = AUDIT / "DAY9_MATCHED_POOL_GPQA_PER_PROMPT_RESULTS.csv"
CONFIG = AUDIT / "DAY9_MATCHED_POOL_GPQA_ROUTER_CONFIG.txt"

FEATURES = [
    "char_count", "word_count", "line_count", "digit_count",
    "question_mark_count", "exclamation_count", "code_symbol_count",
    "contains_code_fence", "contains_url", "contains_equation_symbol",
    "contains_question_word",
]
ALPHAS = [0.1, 1.0, 10.0, 100.0]
SEED = 2026
CANDIDATES = [
    "claude-sonnet-4", "deepseek-r1-0528", "deepseek-v3.1-terminus",
    "deepseek-v3-0324", "gemini-2.5-flash", "gemini-2.5-pro", "glm-4.6",
    "gpt-5", "gpt-5-chat", "intern-s1", "kimi-k2-0905",
    "qwen3-235b-a22b-2507", "qwen3-235b-a22b-thinking-2507",
]
BOOTSTRAPS = 10000

# Load only the feature function from the existing script, without
# executing its archive-extraction workflow.
source_code = (ROOT / "extract_prompt_features.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source_code)
feature_def = next(
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "feature_row"
)
isolated = ast.Module(
    body=[ast.Import(names=[ast.alias(name="re")]), feature_def],
    type_ignores=[],
)
ast.fix_missing_locations(isolated)
exec(compile(isolated, "existing_feature_row", "exec"), globals())

def fail(message):
    raise SystemExit("STOP: " + message)

# Read the three source domains from the existing feature/score table.
with SOURCE.open(encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if not rows:
    fail(f"Source feature table is empty: {SOURCE}")

source_domains = sorted({r["dataset"] for r in rows})
expected_domains = {
    "arenahard_coding",
    "arenahard_creative_writing",
    "arenahard_math",
}
if set(source_domains) != expected_domains:
    fail(f"Unexpected source domains: {source_domains}")

meta_columns = {"dataset", "index", "prompt_text_source", *FEATURES}
available_models = set(rows[0]) - meta_columns
missing_candidates = sorted(set(CANDIDATES) - available_models)
if missing_candidates:
    fail(f"Matched candidate models missing from source table: {missing_candidates}")
model_names = CANDIDATES.copy()
if len(model_names) != 13 or len(set(model_names)) != 13:
    fail("Matched candidate pool must contain exactly 13 unique models.")

X = np.array(
    [[float(r[c]) for c in FEATURES] for r in rows],
    dtype=float,
)
Y = np.array(
    [[float(r[m]) for m in model_names] for r in rows],
    dtype=float,
)
domains = np.array([r["dataset"] for r in rows])

if not np.isfinite(X).all() or not np.isfinite(Y).all():
    fail("Source table contains missing or non-finite feature/score values.")

# Hold out 20% of each source domain for alpha selection.
rng = np.random.default_rng(SEED)
train_indices, val_indices = [], []
for domain in source_domains:
    indices = np.flatnonzero(domains == domain)
    if len(indices) < 5:
        fail(f"Too few source prompts in {domain}: {len(indices)}")
    indices = rng.permutation(indices)
    n_val = max(1, int(round(0.20 * len(indices))))
    val_indices.extend(indices[:n_val])
    train_indices.extend(indices[n_val:])

train_indices = np.array(sorted(train_indices), dtype=int)
val_indices = np.array(sorted(val_indices), dtype=int)

# Select alpha by equal-weight average routing utility across source domains.
alpha_results = []
for alpha in ALPHAS:
    predictors = []
    for j in range(len(model_names)):
        model = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
        model.fit(X[train_indices], Y[train_indices, j])
        predictors.append(model)

    predictions = np.column_stack([
        model.predict(X[val_indices]) for model in predictors
    ])
    selected = predictions.argmax(axis=1)
    actual = Y[val_indices, :][np.arange(len(val_indices)), selected]

    per_domain = {
        d: float(np.mean(actual[domains[val_indices] == d]))
        for d in source_domains
    }
    alpha_results.append((float(np.mean(list(per_domain.values()))), alpha, per_domain))

# Select highest validation utility; on ties prefer stronger regularization.
best_utility, best_alpha, best_domain_utility = max(
    alpha_results,
    key=lambda item: (item[0], item[1]),
)
# Select the global baseline on the same source-only validation split as Day 6.
# This makes the GPQA analysis protocol-aligned with the 13-model MMLU-Pro run.
global_means = {}
for j, model in enumerate(model_names):
    global_means[model] = float(np.mean([
        Y[val_indices[domains[val_indices] == d], j].mean()
        for d in source_domains
    ]))
global_model = max(model_names, key=lambda m: global_means[m])

# Fit the frozen router on all source prompts.
final_models = []
for j in range(len(model_names)):
    model = make_pipeline(StandardScaler(), Ridge(alpha=best_alpha))
    model.fit(X, Y[:, j])
    final_models.append(model)

# Save source-only configuration before opening GPQA result files.
with CONFIG.open("w", encoding="utf-8") as f:
    f.write("DAY 9 — MATCHED-POOL SOURCE-ONLY ROUTER CONFIGURATION\n")
    f.write(f"Source rows: {len(rows)}\n")
    f.write(f"Source domains: {', '.join(source_domains)}\n")
    f.write(f"Candidate models: {len(model_names)}\n")
    f.write("Matched 13-model candidate pool shared with Day 6 MMLU-Pro.\n")
    f.write("Global baseline selected on the same source validation split as alpha.\n")
    f.write(f"Alpha candidates: {ALPHAS}\n")
    f.write(f"Selected alpha: {best_alpha}\n")
    f.write(f"Global baseline model: {global_model}\n")
    f.write(f"Global baseline source macro-mean: {global_means[global_model]:.8f}\n")
    f.write("GPQA scores were not read during source fitting or selection.\n")
    f.write("\nValidation utility by alpha:\n")
    for utility, alpha, per_domain in alpha_results:
        f.write(f"alpha={alpha}: macro_utility={utility:.8f}; {per_domain}\n")

# Load GPQA metadata and the exact candidate model files.
with META.open(encoding="utf-8-sig", newline="") as f:
    metadata = list(csv.DictReader(f))

gpqa_meta = [
    r for r in metadata
    if "gpqa" in r["dataset"].lower()
    and r["model"] in model_names
]
if len(gpqa_meta) != len(CANDIDATES):
    fail(
        f"Expected exactly {len(CANDIDATES)} GPQA metadata rows for the matched candidate pool "
        f"before split/demo validation; found {len(gpqa_meta)}"
    )

invalid_split = [
    r["model"] for r in gpqa_meta
    if r["split"].strip().lower() != "test"
]
if invalid_split:
    fail("GPQA candidate metadata contains non-test records: " + ", ".join(invalid_split))

invalid_demo = [
    r["model"] for r in gpqa_meta
    if r["demo"].strip().lower() not in {"false", "0"}
]
if invalid_demo:
    fail("GPQA candidate metadata contains demonstration records: " + ", ".join(invalid_demo))

if len({r["model"] for r in gpqa_meta}) != len(CANDIDATES):
    fail("GPQA metadata has duplicate or missing matched candidate model entries.")

if {r["split"].strip().lower() for r in gpqa_meta} != {"test"}:
    fail("GPQA metadata split is not exclusively test.")
if {r["demo"].strip().lower() for r in gpqa_meta} - {"false", "0"}:
    fail("GPQA metadata demo flag is not exclusively false.")

gpqa_records = defaultdict(dict)
gpqa_texts = defaultdict(dict)
archive_errors = []

with tarfile.open(ARCHIVE, "r:gz") as tar:
    members = {
        m.name.lstrip("./"): m for m in tar.getmembers() if m.isfile()
    }
    for meta in gpqa_meta:
        member_name = meta["archive_path"].lstrip("./")
        member = members.get(member_name)
        if member is None:
            archive_errors.append(f"Missing archive member: {member_name}")
            continue
        try:
            handle = tar.extractfile(member)
            if handle is None:
                raise ValueError("Could not read archive member")
            payload = json.load(handle)
            records = payload.get("records", [])
            if not isinstance(records, list):
                raise ValueError("records is not a list")
            for rec in records:
                idx = str(rec.get("index", ""))
                origin = rec.get("origin_query")
                prompt = rec.get("prompt")
                text_value = (
                    origin if isinstance(origin, str) and origin.strip()
                    else prompt
                )
                if not idx or not isinstance(text_value, str) or not text_value.strip():
                    raise ValueError(f"Missing index/prompt in {member_name}")
                score = rec.get("score")
                if score is None:
                    raise ValueError(f"Missing score: {member_name}, index={idx}")
                score = float(score)
                if not np.isfinite(score):
                    raise ValueError(f"Non-finite score: {member_name}, index={idx}")
                if idx in gpqa_records[meta["model"]]:
                    raise ValueError(f"Duplicate index: {meta['model']}, {idx}")
                gpqa_records[meta["model"]][idx] = score
                gpqa_texts[meta["model"]][idx] = text_value
        except Exception as exc:
            archive_errors.append(f"{member_name}: {type(exc).__name__}: {exc}")

if archive_errors:
    fail("GPQA archive errors:\n" + "\n".join(archive_errors[:10]))

# Confirm every candidate has exactly the same 198 prompts in the same order.
first_model = model_names[0]
prompt_order = list(gpqa_records[first_model].keys())
if len(prompt_order) != 198:
    fail(f"Expected 198 GPQA prompts, found {len(prompt_order)} for {first_model}")

for model in model_names:
    if list(gpqa_records[model].keys()) != prompt_order:
        fail(f"Prompt order/index mismatch for GPQA model {model}")
    for idx in prompt_order:
        if gpqa_texts[model][idx] != gpqa_texts[first_model][idx]:
            fail(f"Prompt text mismatch at GPQA index {idx}, model {model}")

# Apply the frozen router; only now are GPQA scores used for evaluation.
gpqa_X = np.array(
    [
        [feature_row(gpqa_texts[first_model][idx])[name] for name in FEATURES]
        for idx in prompt_order
    ],
    dtype=float,
)
if gpqa_X.shape != (198, len(FEATURES)):
    fail(f"Unexpected GPQA feature shape: {gpqa_X.shape}")

predicted = np.column_stack([m.predict(gpqa_X) for m in final_models])
router_choice = predicted.argmax(axis=1)
router_model_names = np.array(model_names)[router_choice]

router_scores = np.array([
    gpqa_records[router_model_names[i]][idx]
    for i, idx in enumerate(prompt_order)
], dtype=float)
global_scores = np.array([
    gpqa_records[global_model][idx] for idx in prompt_order
], dtype=float)

differences = router_scores - global_scores
rng_boot = np.random.default_rng(SEED)
boot_means = np.empty(BOOTSTRAPS, dtype=float)
n = len(differences)
for start in range(0, BOOTSTRAPS, 200):
    end = min(start + 200, BOOTSTRAPS)
    sampled = rng_boot.integers(0, n, size=(end - start, n))
    boot_means[start:end] = differences[sampled].mean(axis=1)
ci_low, ci_high = np.quantile(boot_means, [0.025, 0.975])

wins = int(np.sum(differences > 0))
ties = int(np.sum(differences == 0))
losses = int(np.sum(differences < 0))

with DETAIL.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "index", "router_model", "router_score",
        "global_model", "global_score", "paired_difference"
    ])
    for i, idx in enumerate(prompt_order):
        writer.writerow([
            idx, router_model_names[i], router_scores[i],
            global_model, global_scores[i], differences[i]
        ])

with OUT.open("w", encoding="utf-8") as f:
    f.write("DAY 9 — MATCHED-POOL HELD-OUT GPQA TRANSFER EVALUATION\n")
    f.write("=" * 48 + "\n")
    f.write("Protocol: source-only tuning and baseline selection; GPQA held out.\n")
    f.write(f"Source domains: {', '.join(source_domains)}\n")
    f.write(f"Source prompts: {len(rows)}\n")
    f.write(f"Candidate models compared: {len(model_names)}\n")
    f.write("Candidate pool: same 13 models used in Day 6 MMLU-Pro.\n")
    f.write("Global baseline selected on source validation split, matching Day 6.\n")
    f.write(f"GPQA evaluation prompts: {len(prompt_order)}\n")
    f.write(f"Selected alpha: {best_alpha}\n")
    f.write(f"Global baseline model: {global_model}\n\n")
    f.write(f"Router mean GPQA score: {router_scores.mean():.6f}\n")
    f.write(f"Global baseline mean GPQA score: {global_scores.mean():.6f}\n")
    f.write(f"Mean paired difference (router - global): {differences.mean():.6f}\n")
    f.write(f"95% prompt-bootstrap percentile CI: [{ci_low:.6f}, {ci_high:.6f}]\n")
    f.write(f"Prompt wins / ties / losses: {wins} / {ties} / {losses}\n")
    f.write(f"Bootstrap resamples: {BOOTSTRAPS}; seed: {SEED}\n\n")
    f.write("Interpretation guardrails:\n")
    f.write("- This estimates performance on this GPQA sample only.\n")
    f.write("- A confidence interval including zero does not establish improvement.\n")
    f.write("- The prompt bootstrap treats prompts as resampling units.\n")
    f.write("- No broad-domain generalization or novelty claim follows from this result.\n")
    f.write("- Model scores are benchmark-provided scores; scoring semantics still matter.\n")
    f.write(f"\nPer-prompt output: {DETAIL}\n")
    f.write(f"Source-only config: {CONFIG}\n")

print("DAY 9 MATCHED-POOL GPQA TRANSFER RUN COMPLETE")
print(f"Source prompts: {len(rows)}")
print(f"Validation-selected alpha: {best_alpha}")
print(f"Source-selected global baseline: {global_model}")
print(f"GPQA prompts: {len(prompt_order)}")
print(f"Router mean score: {router_scores.mean():.6f}")
print(f"Global mean score: {global_scores.mean():.6f}")
print(f"Mean paired difference: {differences.mean():.6f}")
print(f"95% bootstrap CI: [{ci_low:.6f}, {ci_high:.6f}]")
print(f"Wins/ties/losses: {wins}/{ties}/{losses}")
print(f"Report: {OUT}")
print(f"Per-prompt CSV: {DETAIL}")
print(f"Source-only config: {CONFIG}")
