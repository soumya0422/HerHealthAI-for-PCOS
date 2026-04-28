# HerHealthAI — Project Documentation

> **PCOS Risk Assessment & Lifestyle Guide**
> A full-stack AI-powered platform for Polycystic Ovary Syndrome (PCOS) risk prediction with personalised health recommendations.

---

## Table of Contents

- [How the Project Works](#how-the-project-works)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Active Files (Currently In Use)](#active-files-currently-in-use)
- [Optional / Not In Use Files](#optional--not-in-use-files)
- [Key Feature: Tree Interpreter Key Factors](#key-feature-tree-interpreter-key-factors)

---

## How the Project Works

```
User opens browser → Frontend (index.html + app_v3.js)
                        ↓
              Fills PCOS Assessment Form
                        ↓
              POST /predict or /predict/full
                        ↓
         FastAPI Backend (app/main.py)
                        ↓
         ML Inference (app/ml/inference.py)
           ├── Builds feature vector from user input
           ├── Scales features with StandardScaler
           ├── RandomForest predicts PCOS probability
           ├── Tree Interpreter computes key contributing factors
           └── Returns risk %, level, confidence, top 10 factors
                        ↓
         Gemini AI generates personalised recommendations
                        ↓
         Frontend renders results with animated gauge,
         color-coded key factors chart, diet/exercise plans
```

---

## How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set environment variables in .env
#    GEMINI_API_KEY=your_key_here

# 3. Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Open browser
#    http://localhost:8000
```

---

## Project Structure

```
HerHealthAI/
├── app/                          # ★ MAIN BACKEND (FastAPI)
├── continuous_learning/          # ★ ML RETRAINING PIPELINE
├── frontend/                     # ★ USER INTERFACE
├── kubernetes/                   # Deployment configs
├── Backend.py                    # ⚠ LEGACY (not in use)
├── llm.py                        # ⚠ TEST SCRIPT (not in use)
├── pcos_ml_model.pkl             # ⚠ ORIGINAL MODEL (superseded)
└── ...config files
```

---

## Active Files (Currently In Use)

### 🔹 Backend — `app/`

| File | Role |
|------|------|
| `app/main.py` | **Entry point.** Creates FastAPI app, registers all routers, serves frontend static files, configures CORS and rate limiting. Start the server by running this file. |
| `app/config.py` | **Settings.** Loads environment variables: `SECRET_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, `FRONTEND_ORIGINS`, token expiry hours. |
| `app/__init__.py` | Package marker (empty). |

### 🔹 API Endpoints — `app/api/endpoints/`

| File | Role |
|------|------|
| `predict.py` | **Core prediction endpoint.** `POST /predict` (anonymous) and `POST /predict/full` (authenticated — saves to DB, gets Gemini recommendations, tracks progress). Also handles `POST /feedback` for continuous learning. |
| `auth.py` | **Authentication.** `POST /auth/register` and `POST /auth/login` — creates users, returns JWT tokens. |
| `profiles.py` | **Multi-profile management.** `GET/POST /profiles/` — allows one user to manage multiple health profiles (e.g., for family members). |
| `health.py` | **System status.** `GET /health` (health check) and `GET /metrics` (model accuracy, F1, AUC stats shown on landing page). |
| `diary.py` | **Cycle diary.** `POST /diary/log` and `GET /diary/history` — menstrual cycle tracking with Gemini-powered insights. |
| `user_records.py` | **History & progress.** `GET /history` and `GET /progress` — retrieves past assessments and tracks improvement over time. |
| `__init__.py` | Package marker. |

### 🔹 ML Engine — `app/ml/`

| File | Role |
|------|------|
| `inference.py` | **★ Brain of the project.** Contains: `build_feature_vector()` (maps user input → 41-feature vector), `_tree_interpreter()` (traces decision paths through every RandomForest tree for exact per-prediction contributions), `_compute_key_factors()` (produces top 10 key factors with direction), `ml_predict()` (main prediction function), `get_gemini_recommendations()` (calls Gemini API for diet/exercise/lifestyle plans), `get_cycle_diary_insights()` (Gemini-powered diary analysis). |
| `model.py` | **Model loader.** `ModelStore` class holds the loaded model, scaler, encoders, feature columns, and feature means in memory. Loads from `continuous_learning/production_model.pkl` on startup. |
| `__init__.py` | Package marker. |

### 🔹 Authentication & Security — `app/core/`

| File | Role |
|------|------|
| `security.py` | **JWT authentication.** `hash_password()`, `verify_password()`, `create_token()`, `decode_token()`, `get_current_user()` — handles bcrypt hashing and HS256 JWT tokens (24h expiry). |
| `utils.py` | **Helpers.** `calculate_age()` — converts DOB string to age integer. |
| `__init__.py` | Package marker. |

### 🔹 Database — `app/db/`

| File | Role |
|------|------|
| `session.py` | **Database connection.** Creates SQLAlchemy engine and session factory using SQLite (`herhealthai.db`). Provides `get_db()` dependency for FastAPI endpoints. |
| `__init__.py` | Package marker. |

### 🔹 Data Models — `app/models/`

| File | Role |
|------|------|
| `database.py` | **ORM models.** Defines `UserModel`, `ProfileModel`, `HealthRecord`, `ProgressRecord` tables — stores users, profiles, prediction history, and improvement tracking. |
| `schemas.py` | **Pydantic schemas.** `PredictRequest` — validates incoming prediction payloads with field constraints (e.g., age 10–80, weight 20–300). |
| `__init__.py` | Package marker (imports and creates all tables). |

---

### 🔹 Continuous Learning Pipeline — `continuous_learning/`

| File | Role |
|------|------|
| `config.py` | **Pipeline config.** Defines file paths (model, metrics, dataset), `EXPECTED_FEATURES` list (41 columns), and improvement threshold for model promotion. |
| `preprocess.py` | **Data preparation.** `get_training_data()` loads original Excel dataset + merges new feedback entries. `preprocess_for_training()` handles label encoding and scaling. |
| `retrain.py` | **Model training.** `train_candidate_model()` — trains a new RandomForestClassifier (200 trees, balanced classes), saves model + scaler + encoders + `feature_means` to pickle. |
| `evaluator.py` | **Model evaluation.** `evaluate_model()` — computes accuracy, precision, recall, F1, ROC-AUC on the training set. |
| `deploy_if_better.py` | **Auto-promotion.** Compares candidate model metrics vs production; promotes if improvement exceeds threshold. Backs up old model. |
| `data_collector.py` | **Telemetry.** `log_prediction()` and `log_feedback()` — stores predictions and clinical feedback in SQLite (`telemetry.db`) for future retraining. |
| `scheduler.py` | **Scheduled retraining.** Uses `APScheduler` to run the retrain→evaluate→deploy pipeline on a daily cron schedule. |
| `test_pipeline.py` | **Pipeline test.** End-to-end test that runs train→evaluate→deploy to verify the pipeline works. |
| `production_model.pkl` | **Active model.** The RandomForest model currently used for predictions (includes scaler, encoders, feature_means). |
| `production_model_metrics.json` | **Model metrics.** Current accuracy, F1, ROC-AUC of the production model. |
| `candidate_metrics.json` | **Candidate metrics.** Metrics of the last trained candidate model before promotion. |
| `telemetry.db` | **Feedback database.** SQLite DB storing prediction logs and clinical feedback (gitignored). |
| `backups/` | **Model backups.** Previous model versions saved before replacement. |

---

### 🔹 Frontend — `frontend/`

| File | Role |
|------|------|
| `index.html` | **Single-page app.** Contains all pages: Landing, Assessment (4-step form), Results (gauge + key factors chart + recommendations tabs), Progress (history chart), Cycle Diary, Login/Register modals. |
| `app_v3.js` | **Application logic.** Handles: page navigation, profile management, form validation, API calls, result rendering, animated gauge, **color-coded key factors chart** (red=increases risk, green=decreases risk via Canvas API), progress chart, diary logging, toast notifications, clinical feedback. |
| `style.css` | **Styling.** Dark-mode glassmorphism design with CSS variables, animations, responsive layout, profile color system. |

---

### 🔹 Config & Deployment

| File | Role |
|------|------|
| `.env.example` | **Environment template.** Shows required env vars: `SECRET_KEY`, `GEMINI_API_KEY`, `DATABASE_URL`, `FRONTEND_ORIGINS`. |
| `.gitignore` | **Git exclusions.** Excludes `.env`, `__pycache__`, `venv`, `scratch/`, `*.db`, `_dev_backup/`. |
| `requirements.txt` | **Python dependencies.** Lists: fastapi, uvicorn, scikit-learn, pandas, numpy, bcrypt, PyJWT, SQLAlchemy, google-genai, slowapi, python-dotenv, openpyxl, apscheduler. |
| `Dockerfile` | **Container build.** Multi-stage Docker image for production deployment. |
| `docker-compose.yml` | **Docker orchestration.** Runs the app container with port mapping and env file. |
| `.dockerignore` | **Docker exclusions.** Excludes venv, git, pycache from Docker context. |
| `kubernetes/deployment.yaml` | **K8s deployment.** Kubernetes Deployment manifest for production scaling. |
| `kubernetes/service.yaml` | **K8s service.** Kubernetes Service manifest for load balancing. |
| `.github/workflows/ci-cd.yml` | **CI/CD pipeline.** GitHub Actions workflow for automated testing and deployment. |
| `LICENSE` | **MIT License.** |
| `README.md` | **Project readme.** Basic project description. |
| `PROJECT_COMPLETE_GUIDE.md` | **Detailed guide.** Comprehensive documentation of every folder and file. |

---

## Optional / Not In Use Files

These files exist in the repo but are **NOT used** by the running application:

| File | Status | Explanation |
|------|--------|-------------|
| `Backend.py` | ⚠️ **LEGACY — NOT IN USE** | The original monolithic backend from v1. All its functionality has been migrated to the modular `app/` package. Kept as reference only. Can be safely deleted. |
| `llm.py` | ⚠️ **TEST SCRIPT — NOT IN USE** | A quick test script that was used to verify Gemini API connectivity. Contains a hardcoded API key (security risk). Should be deleted. |
| `pcos_ml_model.pkl` | ⚠️ **SUPERSEDED — NOT IN USE** | The original trained model from v1. The app now loads from `continuous_learning/production_model.pkl` instead. Kept as fallback reference. |
| `model_metrics.json` | ⚠️ **SUPERSEDED — NOT IN USE** | Original model metrics from v1. The app now reads from `continuous_learning/production_model_metrics.json`. |
| `run_ngrok.ps1` | 🔧 **OPTIONAL** | PowerShell script to create an ngrok tunnel for remote access during development/demos. Not needed for local development. |
| `test_backend.py` | 🔧 **OPTIONAL** | Pytest test suite for API endpoints. Used during development, not required at runtime. |
| `PROJECT_COMPLETE_GUIDE.md` | 📄 **OPTIONAL** | Older version of project documentation. This file (`PROJECT_DOCUMENTATION.md`) is the updated version. |
| `continuous_learning/backups/` | 🔧 **AUTO-GENERATED** | Model backups created automatically during retraining. Not manually edited. |
| `continuous_learning/candidate_metrics.json` | 🔧 **AUTO-GENERATED** | Created during retraining pipeline. Temporary file. |
| `Dockerfile` | 🔧 **OPTIONAL** | Only needed for Docker-based deployment, not for local development. |
| `docker-compose.yml` | 🔧 **OPTIONAL** | Only needed for Docker-based deployment. |
| `kubernetes/` | 🔧 **OPTIONAL** | Only needed for Kubernetes cloud deployment. |
| `.github/workflows/ci-cd.yml` | 🔧 **OPTIONAL** | Only runs on GitHub when code is pushed. Not needed locally. |

---

## Key Feature: Tree Interpreter Key Factors

Located in `app/ml/inference.py`, the `_tree_interpreter()` function provides **exact per-prediction feature contributions**:

### How It Works:

1. For each of the 200 decision trees in the RandomForest:
   - Traces the **decision path** from root to leaf for the patient's input
   - At each split node, credits the splitting feature with the **probability shift** (child prob − parent prob)
2. Averages contributions across all 200 trees
3. Positive contribution = feature **increases** PCOS risk
4. Negative contribution = feature **decreases** PCOS risk
5. Returns top 10 factors sorted by absolute impact, normalised to sum to 100%

### Why It's Better Than Global Importance:

| Aspect | Global Importance (old) | Tree Interpreter (current) |
|--------|------------------------|---------------------------|
| Same for all patients? | ✅ Yes — identical ranking | ❌ No — unique per patient |
| Shows direction? | ❌ No | ✅ Yes (increases/decreases risk) |
| Mathematically exact? | ❌ Approximate | ✅ Contributions sum to (prediction − base rate) |

### Frontend Visualization:

The `drawFeatureChart()` function in `app_v3.js` renders the factors with:
- 🔴 **Red/orange bars** → factors increasing risk
- 🟢 **Green/teal bars** → factors decreasing risk
- ▲/▼ direction arrows and a color legend

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Uvicorn |
| ML Model | scikit-learn RandomForestClassifier (200 trees) |
| AI Recommendations | Google Gemini 2.0 Flash |
| Database | SQLite + SQLAlchemy ORM |
| Authentication | bcrypt + JWT (PyJWT) |
| Frontend | Vanilla HTML/CSS/JS with Canvas charts |
| Deployment | Docker, Kubernetes, GitHub Actions CI/CD |
