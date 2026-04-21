import numpy as np
import pandas as pd
import joblib
import xgboost as xgb
import json
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List
import uvicorn

# 🔹 Phase 2 imports
from pipeline.parser import parse_log
from pipeline.flow import update_flow
from pipeline.features import extract_features
from pipeline.rules import rule_based_detection
from pipeline.blocker import block_ip
from pipeline.chatbot import generate_response
from pipeline.anomly import is_anomaly

# ─────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────
suspicious_queue = []
active_connections = []
recent_logs = []   # 🔥 FIXED (was missing)


with open("selected_features.json") as f:
    SELECTED_FEATURES = json.load(f)

# ─────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────

MODEL_PATH = "xgb_cicids2017.json"
ENCODER_PATH = "label_encoder.pkl"

model = xgb.XGBClassifier()
model.load_model(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)

print("[OK] Model + Encoder Loaded")

# ─────────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(title="SOC AI System", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

# ─────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────

class FlowFeatures(BaseModel):
    Flow_Duration: float = Field(0.0, alias="Flow Duration")
    Total_Fwd_Packets: float = Field(0.0, alias="Total Fwd Packets")
    Flow_Bytes_per_s: float = Field(0.0, alias="Flow Bytes/s")
    Flow_Packets_per_s: float = Field(0.0, alias="Flow Packets/s")
    Average_Packet_Size: float = Field(0.0, alias="Average Packet Size")

    class Config:
        populate_by_name = True


class PredictionResponse(BaseModel):
    predicted_class: str
    confidence: float
    all_probabilities: dict


class BatchRequest(BaseModel):
    flows: List[FlowFeatures]


class BatchResponse(BaseModel):
    predictions: List[PredictionResponse]
    total: int


# ─────────────────────────────────────────────
# WEBSOCKET
# ─────────────────────────────────────────────

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            await asyncio.sleep(10)  # keep connection alive
    except:
        active_connections.remove(websocket)
        
# ─────────────────────────────────────────────
# ML CORE
# ─────────────────────────────────────────────

def features_to_df(flow):
    df = pd.DataFrame([flow.model_dump()])
    df = df.reindex(columns=SELECTED_FEATURES, fill_value=0.0)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    return df


def run_prediction(flow: FlowFeatures) -> PredictionResponse:
    df = features_to_df(flow)

    proba = model.predict_proba(df)[0]
    pred_idx = int(np.argmax(proba))
    classes = label_encoder.classes_

    return PredictionResponse(
        predicted_class=classes[pred_idx],
        confidence=round(float(proba[pred_idx]), 6),
        all_probabilities={
            cls: round(float(p), 6)
            for cls, p in zip(classes, proba)
        }
    )

# ─────────────────────────────────────────────
# BASIC ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse(BASE_DIR / "login.html")


@app.get("/login.html")
def login_page():
    return FileResponse(BASE_DIR / "login.html")


@app.get("/ui.html")
def dashboard_page():
    return FileResponse(BASE_DIR / "ui.html")


@app.get("/api/status")
def api_status():
    return {"status": "ok", "classes": list(label_encoder.classes_)}


@app.post("/predict", response_model=PredictionResponse)
def predict(flow: FlowFeatures):
    return run_prediction(flow)



import uuid

suspicious_queue = []

@app.post("/api/logs/ingest")
def ingest_log(data: dict):
    raw_log = data.get("raw_log")
    ip = data.get("source", "unknown")

    # your model prediction
    prediction = model_predict(raw_log)

    result = {
        "ip": ip,
        "raw_log": raw_log,
        "prediction": prediction
    }

    # 🔥 ADD THIS BLOCK
    if prediction in ["Suspicious", "Unknown", "Anomaly"]:
        suspicious_queue.append({
            "id": str(uuid.uuid4()),
            "ip": ip,
            "log": raw_log,
            "prediction": prediction,
            "status": "pending"
        })

    return {"status": "processed", "prediction": prediction}


# ─────────────────────────────────────────────
# MAIN SOC PIPELINE
# ─────────────────────────────────────────────

@app.post("/logs/ingest")
async def ingest_log(data: dict):
    try:
        raw_log = data.get("raw_log")
        if not raw_log:
            raise HTTPException(400, "raw_log missing")

        # 1. Rule detection
        rule_result = rule_based_detection(raw_log)

        # 2. Parse
        parsed = parse_log(raw_log)
        ip = parsed["src_ip"]

        # 3. Flow + features
        flow = update_flow(parsed)
        features_dict = extract_features(flow)
        flow_features = FlowFeatures(**features_dict)

        # 🔥 4. HARD ANOMALY / EXTREME DETECTION (TOP PRIORITY)
        extreme_behavior = (
            parsed.get("bytes", 0) > 1_000_000 or
            parsed.get("status", 0) >= 500 or
            parsed.get("status", 0) == 999 or
            "crazy" in raw_log.lower() or
            "unknown" in raw_log.lower()
        )

        # 🔥 5. DECISION PIPELINE
        if rule_result:
            final_prediction = rule_result
            confidence = 1.0
            anomaly_flag = False

        else:
            ml_result = run_prediction(flow_features)
            anomaly_flag, anomaly_score_val = is_anomaly(features_dict)

            print("ML Confidence:", ml_result.confidence)
            print("Anomaly Score:", anomaly_score_val)

            # 🔥 HARD OVERRIDE (CRITICAL FIX)
            if extreme_behavior:
                final_prediction = "Suspicious / Unknown Threat"
                confidence = 0.99
                anomaly_flag = True

            elif anomaly_flag or ml_result.confidence < 0.75:
                final_prediction = "Suspicious / Unknown Threat"
                confidence = round(anomaly_score_val, 4)
                anomaly_flag = True

            else:
                final_prediction = ml_result.predicted_class
                confidence = ml_result.confidence

        # 🔥 6. HUMAN-IN-THE-LOOP
        if final_prediction == "Suspicious / Unknown Threat":
            suspicious_queue.append({
                "ip": ip,
                "raw_log": raw_log,
                "features": features_dict,
                "score": confidence
            })
            print("[ALERT] Unknown attack detected → needs review")

        # 🔥 7. SAFE BLOCKING
        block_status = "Not Blocked"
        if final_prediction != "Normal Traffic" and confidence > 0.8:
            print(f"[BLOCKED] Suspicious IP: {ip}")
            block_status = "Simulated Block"

        # 🔥 8. STORE FOR CHATBOT
        recent_logs.append({
            "ip": ip,
            "prediction": final_prediction,
            "confidence": confidence
        })

        if len(recent_logs) > 50:
            recent_logs.pop(0)

        # 🔥 9. WEBSOCKET BROADCAST
        print("Active WS connections:", len(active_connections))

        dead_connections = []
        for conn in active_connections:
            try:
                await conn.send_json({
                    "ip": ip,
                    "prediction": final_prediction,
                    "confidence": confidence,
                    "blocked": block_status,
                    "anomaly": anomaly_flag,
                    "needs_review": final_prediction == "Suspicious / Unknown Threat"
                })
                print("Sent to dashboard:", final_prediction)
            except:
                dead_connections.append(conn)

        for dc in dead_connections:
            active_connections.remove(dc)

        return {
            "ip": ip,
            "final_prediction": final_prediction,
            "confidence": confidence,
            "blocked": block_status,
            "anomaly": anomaly_flag
        }

    except Exception as e:
        raise HTTPException(500, str(e))
#────────────────────────────────────────
# CHATBOT
# ───────────────────────────────────────

@app.post("/chat")
def chat(data: dict):
    try:
        question = data.get("question")
        if not question:
            raise HTTPException(400, "question missing")

        # Limit context (avoid token overflow)
        context_logs = recent_logs[-20:]

        context = "\n".join([
            f"IP: {l['ip']} | Attack: {l['prediction']} | Confidence: {l['confidence']}"
            for l in context_logs
        ])

        response = generate_response(context, question)

        return {"response": response}

    except Exception as e:
        raise HTTPException(500, str(e))

# ─────────────────────────────────────────────
# REVIEW QUEUE
# ─────────────────────────────────────────────

@app.get("/review-queue")
def get_review_queue():
    return {"items": suspicious_queue}


@app.post("/review-action")
def review_action(data: dict):
    review_id = data.get("id")
    ip = data.get("ip")
    action = data.get("action", "reviewed")

    global suspicious_queue
    for item in suspicious_queue:
        if (review_id and item.get("id") == review_id) or (ip and item.get("ip") == ip):
            item["status"] = action

    if action in {"allow", "block", "remove"}:
        suspicious_queue = [
            item for item in suspicious_queue
            if not ((review_id and item.get("id") == review_id) or (ip and item.get("ip") == ip))
        ]

    return {"message": f"{action} applied"}

@app.post("/review-action-legacy")
def review_action_legacy(data: dict):
    review_id = data.get("id")
    action = data.get("action")

    for item in suspicious_queue:
        if item["id"] == review_id:
            item["status"] = action

    return {"message": f"{action} applied"}
# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
