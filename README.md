---
title: HerHealthAI
emoji: 🏥
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 7860
---

# HerHealthAI

PCOS Risk Backend

This FastAPI service trains a model on the provided dataset (default sheet `Full_new`) and exposes endpoints to predict risk percentage, get recommendations, and trigger training.

Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Place your dataset named like `PCOS_data_without_infertility*.xlsx` in the working directory. The service will read the sheet `Full_new` by default.

3. Start the API (development):

```bash
uvicorn backend:app --reload --port 8000
```

Endpoints

- `GET /health` — service status
- `POST /train` — start background training; optional query params `data_path` and `sheet_name`
- `POST /predict` — JSON body: `{ "data": {"BMI": 28.5, "Cycle_length": 35, ...}}` → returns `risk_percentage` and `risk_level`
- `POST /recommend` — returns rule-based lifestyle recommendations

Example: start training (background):

```bash
curl -X POST "http://localhost:8000/train?sheet_name=Full_new"
```

Run Streamlit example frontend:

```bash
pip install streamlit
streamlit run app_streamlit.py
```

Explainability:

- If `shap` is installed the `/predict` response will include `top_explanations` with SHAP contributions.

Artifacts:

- Model artifacts are saved into `artifacts/` and `metrics.json` is written with training metadata.

Notes

- The API writes model artifacts to `artifacts/` and keeps a `latest` artifact names (e.g., `model.joblib`).
- For production, run under an ASGI server (Gunicorn + Uvicorn workers) behind a reverse proxy.
- Configure `DATA_SHEET_NAME`, `ARTIFACT_DIR`, and `FRONTEND_ORIGINS` via environment variables.
