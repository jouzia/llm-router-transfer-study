from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
script = root / "run_prompt_feature_router.py"
audit = root / "day1_audit"

# Preserve the original script and current results.
for name in [
    "run_prompt_feature_router.py",
    "day1_audit\prompt_router_test_predictions.csv",
    "day1_audit\prompt_router_experiment_summary.txt",
]:
    source = root / name
    if not source.exists():
        print(f"STOP: expected file not found: {source}")
        sys.exit(1)
    backup = source.with_name(source.name + ".pre_macro_backup")
    if not backup.exists():
        shutil.copy2(source, backup)
        print(f"Backup: {backup}")

text = script.read_text(encoding="utf-8")

old = """        pooled_train_scores = np.concatenate([
            Y_by_domain[d][fit_indices[d]]
            for d in domains
        ], axis=0)

        global_means = pooled_train_scores.mean(axis=0)
        global_model_index = int(np.argmax(global_means))"""

new = """        # Select one global model by equal-weight macro-average
        # training performance across domains.
        global_domain_means = np.stack([
            Y_by_domain[d][fit_indices[d]].mean(axis=0)
            for d in domains
        ], axis=0)

        global_means = global_domain_means.mean(axis=0)
        global_model_index = int(np.argmax(global_means))"""

if new in text:
    print("The macro-average correction is already present.")
elif old in text:
    script.write_text(text.replace(old, new, 1), encoding="utf-8")
    print("Corrected global selection to use equal-weight domain means.")
else:
    print("STOP: expected code block not found. No patch applied.")
    sys.exit(1)
