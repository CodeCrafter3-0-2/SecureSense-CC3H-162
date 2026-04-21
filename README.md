# SOC AI Threat Intelligence Dashboard

An AI-assisted Security Operations Center (SOC) dashboard for ingesting web/network logs, classifying traffic with a trained CICIDS2017 XGBoost model, surfacing unknown threats for review, and giving analysts a browser-based real-time monitoring UI.

The project combines:

- A FastAPI backend for predictions, log ingestion, WebSocket streaming, review actions, and chatbot responses.
- A single-page dashboard in `ui.html` with charts, live alerts, sample log submission, review queue controls, and a SOC assistant panel.
- A standalone `login.html` page linked to the dashboard through browser `localStorage`.
- A trained XGBoost model artifact, label encoder, and selected feature list.
- A lightweight pipeline for parsing raw logs, creating flow features, applying rules, detecting anomalies, and broadcasting results.

## Project Structure

```text
D:\CT_HACKS
|-- main.py                     # FastAPI backend and HTML serving routes
|-- login.html                  # Login page; redirects to ui.html after auth
|-- ui.html                     # Main SOC dashboard UI
|-- index.html                  # Older/simple dashboard page
|-- xgb_cicids2017.json         # Trained XGBoost model artifact
|-- label_encoder.pkl           # Label encoder used by model outputs
|-- selected_features.json      # Feature order expected by the model
|-- model_train.py              # Full model training pipeline
|-- model1.py                   # Alternate/experimental model script
|-- model.md                    # Short model-training notes
|-- confusion_matrix.png        # Training/evaluation artifact
|-- feature_importance.png      # Training/evaluation artifact
|-- training_curve.png          # Training/evaluation artifact
|-- pipeline\
|   |-- parser.py               # Converts raw logs into normalized fields
|   |-- flow.py                 # Aggregates logs into per-IP/endpoint flows
|   |-- features.py             # Builds CICIDS-like feature dictionaries
|   |-- rules.py                # Rule-based detections
|   |-- anomly.py               # Statistical anomaly scoring
|   |-- blocker.py              # Optional iptables-based blocking helper
|   `-- chatbot.py              # SOC assistant response generation
|-- tools\
|   |-- local_rules.py          # Additional local rule helpers
|   `-- virustotal.py           # VirusTotal integration helper
`-- soc-dashboard\              # Separate React/Vite dashboard experiment
```

## Core Features

- **Frontend login flow**
  - Open `/` or `/login.html`.
  - Login with the current demo credentials: `admin` / `admin123`.
  - Successful login stores `auth=true` in `localStorage` and opens `ui.html`.
  - `ui.html` redirects unauthenticated users back to `login.html`.

- **Real-time dashboard**
  - Shows total logs, detected attacks, blocked/simulated-blocked events, and normal traffic.
  - Displays recent traffic and alert cards.
  - Connects to `ws://localhost:8000/ws/logs` for live detection updates.
  - Falls back to simulated data when the WebSocket/API is unreachable.

- **ML detection pipeline**
  - Parses raw logs.
  - Builds flow-level features.
  - Applies rule-based detection first.
  - Runs the trained XGBoost CICIDS2017 model.
  - Adds statistical anomaly detection for unknown or low-confidence behavior.
  - Queues suspicious unknown events for human review.

- **Human-in-the-loop review**
  - Unknown threats are added to `suspicious_queue`.
  - Dashboard polls `/review-queue`.
  - Analysts can allow or block queued items through `/review-action`.

- **SOC assistant**
  - `/chat` uses recent detection context to answer analyst questions.
  - Intended for concise security summaries, indicators, and recommended actions.

## Requirements

Recommended runtime:

- Python 3.10+
- pip
- A modern browser

Python packages used by the backend/training scripts include:

```text
fastapi
uvicorn
numpy
pandas
joblib
xgboost
pydantic
scikit-learn
matplotlib
seaborn
groq
langchain-core
python-dotenv
requests
```

If you do not already have a `requirements.txt`, install the runtime dependencies manually:

```powershell
python -m pip install fastapi uvicorn numpy pandas joblib xgboost pydantic scikit-learn groq langchain-core python-dotenv requests
```

For model training and chart generation, also install:

```powershell
python -m pip install matplotlib seaborn
```

## Configuration

Create or update `.env` for external integrations:

```text
GROQ_API_KEY="your-groq-api-key"
VIRUS_TOTAL_API="your-virustotal-api-key"
ABUSE_IPDB="your-abuseipdb-api-key"
```

Important security note: do not commit real API keys. If keys have already been committed or shared, rotate them from the provider dashboard.

## Running the App

From the project root:

```powershell
cd D:\CT_HACKS
python main.py
```

Or run Uvicorn directly:

```powershell
uvicorn main:app --reload
```

Then open:

```text
http://localhost:8000/
```

The backend serves:

- `/` -> `login.html`
- `/login.html` -> login page
- `/ui.html` -> dashboard page
- `/api/status` -> JSON health/status response

## Login Flow

Current demo credentials:

```text
Username: admin
Password: admin123
```

This is frontend-only demo authentication. It is useful for project demos but is not production authentication. For production, replace it with backend sessions, signed tokens, password hashing, HTTPS, and access control on API/WebSocket endpoints.

## API Reference

### `GET /`

Serves the login page.

### `GET /login.html`

Serves the login page directly.

### `GET /ui.html`

Serves the SOC dashboard.

### `GET /api/status`

Returns model/server status and model class labels.

Example response:

```json
{
  "status": "ok",
  "classes": ["BENIGN", "DDoS", "PortScan"]
}
```

Actual classes depend on `label_encoder.pkl`.

### `POST /predict`

Runs direct model prediction on a feature payload.

Example request:

```json
{
  "Flow Duration": 1.2,
  "Total Fwd Packets": 5,
  "Flow Bytes/s": 1200,
  "Flow Packets/s": 4,
  "Average Packet Size": 240
}
```

Example response:

```json
{
  "predicted_class": "BENIGN",
  "confidence": 0.9821,
  "all_probabilities": {
    "BENIGN": 0.9821,
    "DDoS": 0.0179
  }
}
```

### `POST /logs/ingest`

Main SOC ingestion endpoint used by the dashboard. Accepts a raw log, parses it, updates flow state, runs rules/ML/anomaly logic, stores recent context, queues unknown threats, and broadcasts the result over WebSocket.

Example request:

```json
{
  "raw_log": "192.168.1.10 GET /index.html 200 1024"
}
```

Example response:

```json
{
  "ip": "192.168.1.10",
  "final_prediction": "Normal Traffic",
  "confidence": 0.94,
  "blocked": "Not Blocked",
  "anomaly": false
}
```

### `POST /chat`

Asks the SOC assistant a question using recent detection context.

Example request:

```json
{
  "question": "Summarize the current suspicious IPs."
}
```

Example response:

```json
{
  "response": "..."
}
```

### `GET /review-queue`

Returns suspicious or unknown items waiting for analyst review.

Example response:

```json
{
  "items": [
    {
      "ip": "10.10.0.21",
      "raw_log": "...",
      "features": {},
      "score": 0.99
    }
  ]
}
```

### `POST /review-action`

Applies an analyst action to a queued item.

Example request:

```json
{
  "ip": "10.10.0.21",
  "action": "block"
}
```

Supported action values currently used by the UI:

- `allow`
- `block`
- `remove`

### `WebSocket /ws/logs`

Streams live detection updates to the dashboard.

Example message:

```json
{
  "ip": "10.0.0.55",
  "prediction": "Suspicious / Unknown Threat",
  "confidence": 0.99,
  "blocked": "Simulated Block",
  "anomaly": true,
  "needs_review": true
}
```

## Detection Pipeline

The main `/logs/ingest` route follows this sequence:

1. **Raw log validation**
   - Requires `raw_log`.
   - Returns HTTP 400 if missing.

2. **Rule-based detection**
   - Checks known signatures such as SQL injection and ARP anomaly/MITM-style logs.
   - Rule matches take priority over ML predictions.

3. **Parsing**
   - `pipeline/parser.py` extracts:
     - timestamp
     - source IP
     - method
     - endpoint
     - status
     - byte count

4. **Flow tracking**
   - `pipeline/flow.py` aggregates repeated events by `(src_ip, endpoint)`.
   - Tracks packet count, total bytes, start time, and end time.

5. **Feature extraction**
   - `pipeline/features.py` converts flow state into a feature dictionary.
   - `main.py` aligns features to `selected_features.json`.

6. **XGBoost prediction**
   - Loads `xgb_cicids2017.json`.
   - Uses `label_encoder.pkl` for readable class names.
   - Returns predicted class, confidence, and all class probabilities.

7. **Anomaly override**
   - `pipeline/anomly.py` computes a simple z-score based anomaly score.
   - Extreme byte counts, server errors, unknown markers, and low-confidence predictions can be marked as `Suspicious / Unknown Threat`.

8. **Review queue and broadcast**
   - Unknown threats are appended to `suspicious_queue`.
   - Detection results are pushed to connected dashboard clients over WebSocket.

## Model Training

The training workflow is documented briefly in `model.md` and implemented primarily in `model_train.py`.

Training pipeline highlights:

- Loads and cleans CICIDS2017-style flow data.
- Encodes labels with `LabelEncoder`.
- Handles class imbalance with sample weights.
- Trains an XGBoost classifier.
- Uses regularization:
  - L1: `reg_alpha`
  - L2: `reg_lambda`
  - `gamma`
  - `max_depth`
  - `min_child_weight`
  - `subsample`
  - `colsample_bytree`
  - `colsample_bylevel`
  - `learning_rate`
  - early stopping
- Exports:
  - `xgb_cicids2017.json`
  - `label_encoder.pkl`
  - `selected_features.json`
  - `training_curve.png`
  - `confusion_matrix.png`
  - `feature_importance.png`

To retrain, make sure the expected CICIDS2017 dataset path exists in the training script, then run:

```powershell
python model_train.py
```

## Dashboard Usage

1. Start the backend.
2. Open `http://localhost:8000/`.
3. Log in with the demo credentials.
4. Use the sample log buttons to submit normal, DDoS-like, scan-like, or brute-force-like logs.
5. Watch the cards, charts, recent traffic, and alert feed update.
6. Review unknown threats in the review queue.
7. Ask the SOC assistant questions about recent activity.

## Example Manual Tests

Health/status:

```powershell
Invoke-RestMethod http://localhost:8000/api/status
```

Submit a normal-looking log:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/logs/ingest `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"raw_log":"192.168.1.10 GET /index.html 200 1024"}'
```

Submit an anomalous log:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/logs/ingest `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"raw_log":"10.0.0.55 GET /api/v1/data 200 1500000"}'
```

Fetch review queue:

```powershell
Invoke-RestMethod http://localhost:8000/review-queue
```

## Troubleshooting

### `404 Not Found` for `/login.html` or `/ui.html`

Make sure you are running the updated FastAPI app from the project root:

```powershell
cd D:\CT_HACKS
uvicorn main:app --reload
```

The routes are defined in `main.py`; opening raw files through a different server may not use those routes.

### Dashboard redirects back to login

`ui.html` checks:

```javascript
localStorage.getItem("auth") === "true"
```

Log in through `login.html` first, or clear browser storage and log in again.

### Dashboard shows simulated data

The dashboard falls back to simulation when the WebSocket cannot connect. Confirm the backend is running and that the browser can reach:

```text
ws://localhost:8000/ws/logs
```

### `/chat` fails

Check that the Groq API key is configured and valid. The current `pipeline/chatbot.py` should be updated to read from `.env` instead of embedding secrets directly in source code.

### Model load fails

Confirm these files exist in the project root:

- `xgb_cicids2017.json`
- `label_encoder.pkl`
- `selected_features.json`

Run the server from `D:\CT_HACKS`, because the current paths are relative.

### `iptables` blocking fails on Windows

`pipeline/blocker.py` uses Linux `iptables`. On Windows, blocking is simulated by the dashboard/backend logic unless you replace the blocker with a Windows Firewall implementation.

## Known Issues and Cleanup Ideas

- `pipeline/chatbot.py` currently contains a hardcoded API key. Move it to `.env` and load it with `os.getenv`.
- `main.py` has two functions named `ingest_log` mapped to different routes. FastAPI can still register both routes, but unique function names would be clearer.
- `pipeline/rules.py` defines `rule_based_detection` twice; the second definition overrides the first. Merge both rule sets into one function.
- `pipeline/anomly.py` is misspelled. Consider renaming it to `anomaly.py` and updating imports.
- The login system is frontend-only demo auth. Add real backend authentication before using this beyond a controlled demo.
- `cicids2017_cleaned.csv` is currently empty in this workspace. Retraining requires a real dataset file.
- The React/Vite app in `soc-dashboard` appears separate from the active `ui.html` dashboard. Decide whether to keep it as an experiment or migrate the UI fully to React.

## Security Notes

This project is suitable for demos, experiments, and controlled lab environments. Before production use:

- Remove hardcoded secrets from source files.
- Rotate any exposed keys.
- Add backend authentication and authorization.
- Protect WebSocket and API routes.
- Add request validation and rate limits.
- Store review queues and logs in a durable database instead of in-memory lists.
- Use HTTPS.
- Avoid executing firewall commands without strong safeguards and audit logging.

## License

No license file is currently included. Add a `LICENSE` file before distributing or publishing the project.
