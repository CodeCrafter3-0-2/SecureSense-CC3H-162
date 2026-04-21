import pandas as pd
import numpy as np
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import warnings
warnings.filterwarnings("ignore")

from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)
from sklearn.utils.class_weight import compute_sample_weight

CSV_PATH   = "cicids2017_cleaned.csv"   # <-- path to your cleaned CSV
LABEL_COL  = "Attack Type"              # <-- your attack/benign column name
TEST_SIZE  = 0.2
RANDOM_STATE = 42
MODEL_OUT  = "xgb_cicids2017.json"
ENCODER_OUT = "label_encoder.pkl"

# ─────────────────────────────────────────────
# REGULARIZATION SETTINGS  (tune these)
# ─────────────────────────────────────────────
# L1 regularization on leaf weights — increases sparsity, removes
# noisy/redundant features (e.g. correlated IAT stats). Higher = sparser.
REG_ALPHA        = 0.1       # L1  (0 = off, try: 0.01, 0.1, 1.0, 10)

# L2 regularization on leaf weights — smooths leaf scores, reduces variance.
# XGBoost default is 1. Higher = more shrinkage.
REG_LAMBDA       = 2.0       # L2  (default 1, try: 1, 2, 5, 10)

# Minimum loss reduction to make a split. Acts as a pruner — any split
# that doesn't reduce loss by at least gamma is discarded.
GAMMA            = 0.2       # (0 = off, try: 0, 0.1, 0.5, 1.0)

# Maximum tree depth. Deeper = more complex = more overfit.
MAX_DEPTH        = 6         # (try: 4, 6, 8)

# Minimum sum of instance weights in a leaf. Stops splitting on tiny
# minority-class clusters that are just noise.
MIN_CHILD_WEIGHT = 5         # (try: 1, 5, 10, 20)

# Fraction of rows sampled per tree — row-level bagging.
SUBSAMPLE        = 0.8       # (try: 0.6, 0.8, 1.0)

# Fraction of features sampled per tree — feature dropout.
COLSAMPLE_BYTREE  = 0.8      # (try: 0.5, 0.8, 1.0)

# Fraction of features sampled per depth level — finer-grained dropout.
COLSAMPLE_BYLEVEL = 0.8      # (try: 0.5, 0.8, 1.0)

# Shrinks each tree's contribution. Lower rate + more trees = better
# generalisation but slower training.
LEARNING_RATE    = 0.05      # (try: 0.01, 0.05, 0.1)

N_ESTIMATORS     = 1000      # high ceiling; early stopping will cut it short

EARLY_STOPPING   = 50

print("Loading dataset...")
df = pd.read_csv(CSV_PATH)

df.columns = df.columns.str.strip()

print(f"  Shape: {df.shape}")
print(f"  Label distribution:\n{df[LABEL_COL].value_counts()}\n")


print("Cleaning data...")
df.replace([np.inf, -np.inf], np.nan, inplace=True)
before = len(df)
df.dropna(inplace=True)
print(f"  Dropped {before - len(df)} rows with inf/nan")

X = df.drop(columns=[LABEL_COL])
y_raw = df[LABEL_COL]

X = X.select_dtypes(include=[np.number])
print(f"  Features used: {X.shape[1]}")

le = LabelEncoder()
y = le.fit_transform(y_raw)
n_classes = len(le.classes_)
print(f"\n  Classes ({n_classes}): {list(le.classes_)}\n")

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y,
)
X_train, X_val, y_train, y_val = train_test_split(
    X_train, y_train,
    test_size=0.1,
    random_state=RANDOM_STATE,
    stratify=y_train,
)
print(f"Train: {len(X_train):,}   Val: {len(X_val):,}   Test: {len(X_test):,}")

sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)

model = xgb.XGBClassifier(
    # ── Ensemble size & learning ──────────────
    n_estimators      = N_ESTIMATORS,
    learning_rate     = LEARNING_RATE,      # shrinkage: each tree contributes less

    # ── Tree structure (complexity control) ───
    max_depth         = MAX_DEPTH,          # cap tree depth → less overfit
    min_child_weight  = MIN_CHILD_WEIGHT,   # min leaf weight → no tiny leaf fits

    # ── Regularization terms ──────────────────
    gamma             = GAMMA,              # min loss-reduction to split (pruning)
    reg_alpha         = REG_ALPHA,          # L1: sparsify leaf weights
    reg_lambda        = REG_LAMBDA,         # L2: shrink leaf weights

    # ── Stochastic (dropout-style) ────────────
    subsample         = SUBSAMPLE,          # row bagging per tree
    colsample_bytree  = COLSAMPLE_BYTREE,   # feature dropout per tree
    colsample_bylevel = COLSAMPLE_BYLEVEL,  # feature dropout per depth level

    # ── Multi-class ───────────────────────────
    objective         = "multi:softprob",
    num_class         = n_classes,
    eval_metric       = "mlogloss",

    # ── Early stopping ────────────────────────
    early_stopping_rounds = EARLY_STOPPING,

    # ── Speed / hardware ─────────────────────
    tree_method       = "hist",
    device            = "cpu",              # change to "cuda" if GPU available
    n_jobs            = -1,

    random_state      = RANDOM_STATE,
    verbosity         = 1,
)

model.fit(
    X_train, y_train,
    sample_weight      = sample_weights,
    eval_set           = [(X_val, y_val)],  # early stopping watches val loss
    verbose            = 50,
)

print(f"\n  Best iteration : {model.best_iteration}")
print(f"  Best val score : {model.best_score:.6f}")

print("\n── Evaluation ──────────────────────────────")
y_pred = model.predict(X_test)

acc     = accuracy_score(y_test, y_pred)
f1_mac  = f1_score(y_test, y_pred, average="macro",    zero_division=0)
f1_wt   = f1_score(y_test, y_pred, average="weighted", zero_division=0)

print(f"  Accuracy          : {acc:.4f}")
print(f"  F1 (macro)        : {f1_mac:.4f}")
print(f"  F1 (weighted)     : {f1_wt:.4f}")
print()
print(classification_report(
    y_test, y_pred,
    target_names=le.classes_,
    zero_division=0,
))


results = model.evals_result()
val_loss = results["validation_0"]["mlogloss"]
rounds   = range(1, len(val_loss) + 1)

plt.figure(figsize=(9, 4))
plt.plot(rounds, val_loss, color="steelblue", linewidth=1.5, label="Val log-loss")
plt.axvline(model.best_iteration, color="tomato", linestyle="--",
            label=f"Best round ({model.best_iteration})")
plt.title("XGBoost — Validation Log-Loss (early stopping)")
plt.xlabel("Boosting round")
plt.ylabel("Log-loss")
plt.legend()
plt.tight_layout()
plt.savefig("training_curve.png", dpi=150)
print("  Saved: training_curve.png")


cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(max(8, n_classes), max(6, n_classes - 1)))
sns.heatmap(
    cm,
    annot=True, fmt="d",
    xticklabels=le.classes_,
    yticklabels=le.classes_,
    cmap="Blues",
)
plt.title("XGBoost — Confusion Matrix (CICIDS2017)")
plt.ylabel("True label")
plt.xlabel("Predicted label")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=150)
print("  Saved: confusion_matrix.png")


feat_imp = pd.Series(
    model.feature_importances_,
    index=X_train.columns,
).sort_values(ascending=False).head(20)

plt.figure(figsize=(9, 6))
feat_imp.sort_values().plot(kind="barh", color="steelblue")
plt.title("Top 20 Feature Importances — XGBoost")
plt.xlabel("Importance score")
plt.tight_layout()
plt.savefig("feature_importance.png", dpi=150)
print("  Saved: feature_importance.png")


model.save_model(MODEL_OUT)
joblib.dump(le, ENCODER_OUT)
print(f"\n  Model saved  → {MODEL_OUT}")
print(f"  Encoder saved→ {ENCODER_OUT}")

print("\n── Quick inference example ─────────────────")
sample = X_test.iloc[:5]
preds  = model.predict(sample)
labels = le.inverse_transform(preds)
print("  Predicted classes:", labels)