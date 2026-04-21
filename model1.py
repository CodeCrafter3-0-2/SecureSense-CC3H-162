import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import json

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, f1_score

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

CSV_PATH = "cicids2017_cleaned.csv"
LABEL_COL = "Attack Type"

MODEL_OUT = "xgb_cicids2017.json"
ENCODER_OUT = "label_encoder.pkl"
FEATURES_OUT = "selected_features.json"

# 🔥 YOUR SELECTED FEATURES
TOP_FEATURES = [
    "Max Packet Length",
    "Bwd Packet Length Min",
    "Idle Mean",
    "PSH Flag Count",
    "Idle Min",
    "Bwd Packet Length Mean",
    "Min Packet Length",
    "act_data_pkt_fwd",
    "Bwd Header Length",
    "Total Fwd Packets",
    "Packet Length Mean",
    "Destination Port",
    "min_seg_size_forward",
    "Flow Duration",
    "Active Max",
    "Bwd Packet Length Std",
    "Fwd Header Length",
    "Init_Win_bytes_backward",
    "FIN Flag Count",
    "ACK Flag Count"
]

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────

print("Loading dataset...")
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()

# Clean
df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)

# 🔥 Use only selected features
X = df[TOP_FEATURES]
y_raw = df[LABEL_COL]

# Encode labels
le = LabelEncoder()
y = le.fit_transform(y_raw)

print("Classes:", list(le.classes_))

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ─────────────────────────────────────────────
# MODEL
# ─────────────────────────────────────────────

model = xgb.XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    eval_metric="mlogloss",
    num_class=len(le.classes_),
    tree_method="hist",
    random_state=42,
)

# Train
model.fit(X_train, y_train)

# ─────────────────────────────────────────────
# EVALUATION
# ─────────────────────────────────────────────

y_pred = model.predict(X_test)

print("\nAccuracy:", accuracy_score(y_test, y_pred))
print("F1 (macro):", f1_score(y_test, y_pred, average="macro"))
print("\n", classification_report(y_test, y_pred, target_names=le.classes_))

# ─────────────────────────────────────────────
# SAVE EVERYTHING
# ─────────────────────────────────────────────

model.save_model(MODEL_OUT)
joblib.dump(le, ENCODER_OUT)

with open(FEATURES_OUT, "w") as f:
    json.dump(TOP_FEATURES, f)

print("\nSaved:")
print("✔ Model →", MODEL_OUT)
print("✔ Encoder →", ENCODER_OUT)
print("✔ Features →", FEATURES_OUT)