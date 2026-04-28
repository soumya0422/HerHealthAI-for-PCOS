# HerHealthAI - Complete Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [File Structure & Descriptions](#file-structure--descriptions)
3. [Essential vs Optional Files](#essential-vs-optional-files)
4. [Step-by-Step Setup Guide](#step-by-step-setup-guide)
5. [Running the Project](#running-the-project)
6. [API Documentation](#api-documentation)
7. [Database Schema](#database-schema)
8. [Troubleshooting](#troubleshooting)

---

## Project Overview

**HerHealthAI** is a comprehensive PCOS (Polycystic Ovary Syndrome) risk assessment and health management system built with:
- **Backend**: FastAPI with machine learning inference
- **Frontend**: Responsive HTML/CSS/JavaScript SPA (Single Page Application)
- **Database**: SQLite for user management and health records
- **ML Model**: Random Forest + Gradient Boosting classifier for risk prediction
- **Optional AI**: Google Gemini integration for personalized recommendations

The application provides:
- PCOS risk prediction based on 25+ health metrics
- Personalized lifestyle recommendations
- Menstrual cycle tracking diary
- User authentication and health history
- Model performance metrics and explainability

---

## File Structure & Descriptions

### 📁 ROOT DIRECTORY

#### **ESSENTIAL FILES**

| File | Purpose | Content |
|------|---------|---------|
| `requirements.txt` | Python dependencies | FastAPI, pandas, scikit-learn, streamlit, sqlalchemy, google-genai, PyJWT, passlib, etc. |
| `Dockerfile` | Container image definition | Python 3.11-slim, installs deps, runs uvicorn on port 7860 |
| `app/` | Main application code | FastAPI backend, ML models, database ORM, API endpoints |
| `frontend/` | Web interface | HTML, CSS, JavaScript SPA with particle effects and animations |
| `pcos_ml_model.pkl` | Pre-trained ML model | Serialized Random Forest/XGBoost model (binary classification) |
| `model_metrics.json` | Model performance | Accuracy, precision, recall, F1, ROC-AUC, sample counts |
| `herhealthai.db` | SQLite database | User accounts, health records, diary entries (auto-created if missing) |

#### **OPTIONAL FILES**

| File | Purpose | Usage |
|------|---------|-------|
| `README.md` | Project overview | Quick start guide and endpoint documentation |
| `LICENSE` | MIT License | Legal documentation |
| `docker-compose.yml` | Multi-container setup | Local development with Docker (requires Docker Compose) |
| `test_backend.py` | Unit tests | pytest test cases for endpoints and validation |
| `Backend.py` | Legacy backend | Deprecated - superseded by `app/main.py` |
| `llm.py` | LLM testing script | Test Google Gemini API integration |
| `.gitignore` | Git ignore rules | Exclude venv, __pycache__, .env, etc. |

---

### 📁 APP/ DIRECTORY (Production Backend Code)

#### **Configuration & Core**

| File | Purpose | Responsibility |
|------|---------|-----------------|
| `main.py` | FastAPI entry point | Initializes app, CORS, rate limiting, exception handlers, mounts routers and frontend |
| `config.py` | Configuration management | Loads environment variables (SECRET_KEY, GEMINI_API_KEY, DATABASE_URL, FRONTEND_ORIGINS) |

#### **Security & Database**

| File | Purpose | Responsibility |
|------|---------|-----------------|
| `core/security.py` | Authentication & authorization | Password hashing/verification (bcrypt), JWT token creation/decoding, current user dependency |
| `db/session.py` | Database connection | SQLAlchemy engine, SessionLocal factory, database dependency for FastAPI |

#### **Data Models**

| File | Purpose | Content |
|------|---------|---------|
| `models/database.py` | SQLAlchemy ORM models | 4 tables: `UserModel`, `HealthRecord`, `ProgressRecord`, `MenstrualRecord` |
| `models/schemas.py` | Pydantic validation schemas | Request/response schemas: `RegisterRequest`, `LoginRequest`, `PredictRequest`, `DiaryEntryRequest` |

#### **Machine Learning**

| File | Purpose | Responsibility |
|------|---------|-----------------|
| `ml/model.py` | ML model management | Loads pickled model, scalers, encoders, feature columns, feature importance, metrics |
| `ml/inference.py` | Prediction logic | `build_feature_vector()` - maps inputs to features, `ml_predict()` - inference, Gemini recommendations |

#### **API Endpoints** (`api/endpoints/`)

| File | Purpose | Endpoints |
|------|---------|-----------|
| `health.py` | System health & metrics | `GET /health`, `GET /metrics` |
| `auth.py` | User authentication | `POST /register`, `POST /login`, `GET /me` |
| `predict.py` | PCOS risk prediction | `POST /predict` (anonymous), `POST /predict/full` (authenticated with DB save) |
| `user_records.py` | Health history & recommendations | `GET /history`, `POST /recommend` |
| `diary.py` | Menstrual cycle tracking | `POST /diary/entry` - log cycle data, generates insights |

---

### 📁 FRONTEND/ DIRECTORY (Web User Interface)

| File | Purpose | Content |
|------|---------|---------|
| `index.html` | HTML structure | Multi-page SPA: landing, assessment form, progress dashboard, diary; 25+ input fields, auth modals |
| `app.js` | Frontend logic | State management, form validation, API calls, authentication flow, tab navigation, particle animation |
| `style.css` | Styling | Dark theme with purple/pink gradients, glassmorphism effects, responsive design (mobile/tablet/desktop) |

**Frontend Features:**
- 📱 Responsive design (mobile, tablet, desktop)
- 🎨 Purple/pink gradient with glassmorphism effects
- ✨ Particle background animation
- 📊 Progress tracking dashboard
- 📅 Menstrual cycle diary
- 🔐 User authentication (register/login)
- 💾 Local health history
- 📈 BMI calculator

---

### 📁 KUBERNETES/ DIRECTORY (Production Container Orchestration)

| File | Purpose | Usage |
|------|---------|-------|
| `deployment.yaml` | Kubernetes deployment spec | 3 replicas, health checks, resource limits (256Mi RAM), environment secrets |
| `service.yaml` | Kubernetes service | LoadBalancer exposing port 80 → 8000 |

**Usage**: Deploy to Kubernetes cluster in production environment

---

### 📁 _DEV_BACKUP/ DIRECTORY (Development & Documentation)

#### **Alternative Frontends & Interfaces**

| File | Purpose |
|------|---------|
| `app_streamlit.py` | Alternative Streamlit web UI for quick predictions |

#### **Legacy Code**

| File | Purpose |
|------|---------|
| `Backend.py` | Deprecated backend implementation (use `app/main.py` instead) |

#### **ML Training & Analysis**

| File | Purpose |
|------|---------|
| `train_ml_model.py` | ML training script - loads PCOS dataset, trains Random Forest + XGBoost, saves pickle model |
| `data_analysis.py` | Exploratory data analysis (EDA) of PCOS dataset |

#### **Testing Scripts**

| File | Purpose |
|------|---------|
| `test_api_live.py` | Integration tests against live API endpoints |
| `test_direct_prediction.py` | Direct model pickle loading and inference test |
| `test_model_integration.py` | Full pipeline test with feature mapping |

#### **Documentation**

| File | Purpose |
|------|---------|
| `COMPLETE_PROJECT_GUIDE.md` | Comprehensive project guide |
| `ML_MODEL_TRAINING_REPORT.md` | ML model performance analysis |
| `PROJECT_ANALYSIS_AND_PRODUCTION_ROADMAP.md` | Production deployment strategy |
| `PROJECT_DOCUMENTATION.md` | Full project documentation |

#### **Data & Configuration**

| File | Purpose |
|------|---------|
| `PCOS_data_without_infertility.xlsx` | Original training dataset (541 patient records, 41 medical features) |
| `model_metrics.json` | Development copy of model metrics |
| `herhealthai.db` | Development database snapshot |
| `push_repo.ps1` | PowerShell script for Git operations |
| `run_ngrok.ps1` | Exposes local API to internet via ngrok tunnel |

---

### 📁 SCRATCH/ DIRECTORY (Development Utilities)

| File | Purpose |
|------|---------|
| `inspect_db.py` | CLI tool to inspect database tables and display contents |

---

## Essential vs Optional Files

### ✅ MUST HAVE (Critical for Running)

```
Required Files:
├── app/main.py ........................... FastAPI entry point
├── app/config.py ......................... Configuration
├── app/core/security.py ................. Authentication
├── app/db/session.py .................... Database connection
├── app/models/database.py ............... ORM models
├── app/models/schemas.py ................ Validation schemas
├── app/ml/model.py ...................... ML model loader
├── app/ml/inference.py .................. Prediction logic
├── app/api/endpoints/health.py .......... Health endpoint
├── app/api/endpoints/auth.py ............ Auth endpoint
├── app/api/endpoints/predict.py ......... Prediction endpoint
├── app/api/endpoints/user_records.py .... History endpoint
├── app/api/endpoints/diary.py ........... Diary endpoint
├── requirements.txt ..................... Python dependencies
├── pcos_ml_model.pkl .................... Pre-trained ML model
├── model_metrics.json ................... Model performance metadata
├── frontend/index.html .................. Web UI structure
├── frontend/app.js ...................... Frontend logic
└── frontend/style.css ................... Styling
```

### 🔧 OPTIONAL (Nice to Have, But Not Required)

```
Optional Files:
├── docker-compose.yml ................... Local Docker setup
├── Dockerfile ........................... Container image (for deployment only)
├── test_backend.py ...................... Unit tests
├── README.md ............................ Documentation
├── LICENSE ............................. Legal
├── _dev_backup/app_streamlit.py ........ Alternative frontend
├── _dev_backup/train_ml_model.py ....... Model retraining
├── _dev_backup/*.py .................... Development scripts
├── kubernetes/*.yaml .................... K8s deployment
└── scratch/inspect_db.py ............... Database inspection
```

### 🗂️ AUTO-GENERATED (Created at Runtime)

```
Auto-Generated Files:
├── herhealthai.db ...................... SQLite database (created on first run)
├── .env ................................ Environment variables (must create manually)
└── __pycache__/ ....................... Python cache (auto-created)
```

---

## Step-by-Step Setup Guide

### Prerequisites

- **Python**: 3.10+ (recommended 3.11+)
- **pip**: Python package manager
- **Virtual Environment**: venv or conda
- **Text Editor**: VS Code, PyCharm, or similar
- **Git**: For version control
- **Optional**: Docker & Docker Compose for containerized deployment

### Step 1: Clone Repository & Navigate

```bash
cd c:\Users\HP\OneDrive\Desktop\HerHealthAI
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pandas`, `numpy` - Data processing
- `scikit-learn`, `xgboost` - ML libraries
- `sqlalchemy` - ORM
- `pyjwt`, `passlib[bcrypt]` - Authentication
- `google-genai` - Gemini API (for recommendations)
- `streamlit` - Alternative UI
- `python-dotenv` - Environment variables

### Step 4: Create Environment File

Create `.env` file in project root:

```env
# Secret & Security
SECRET_KEY=herhealthai-super-secret-key-2026-pcos
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Database
DATABASE_URL=sqlite:///./herhealthai.db

# Gemini API (for AI recommendations)
GEMINI_API_KEY=your_gemini_api_key_here

# Frontend CORS
FRONTEND_ORIGINS=*

# Logging
LOG_LEVEL=INFO
```

**To get GEMINI_API_KEY:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Create a new API key
3. Paste it in the `.env` file

### Step 5: Verify ML Model Files

Ensure these files exist in project root:
- ✅ `pcos_ml_model.pkl` - Trained model
- ✅ `model_metrics.json` - Model performance metrics

If missing, you can retrain the model:
```bash
python _dev_backup/train_ml_model.py
```

This requires `PCOS_data_without_infertility.xlsx` in the working directory.

### Step 6: Verify Database (Auto-Created)

The SQLite database (`herhealthai.db`) is created automatically on first run.
To inspect it:
```bash
python scratch/inspect_db.py
```

---

## Running the Project

### Option 1: Development Server (Recommended for Development)

**Start FastAPI Backend:**
```bash
python -m uvicorn app.main:app --reload --port 7860
```

**In another terminal, optionally start Streamlit frontend:**
```bash
streamlit run _dev_backup/app_streamlit.py --server.port 8501
```

**Access:**
- Main UI: http://localhost:7860
- Streamlit UI: http://localhost:8501
- API Docs: http://localhost:7860/docs

### Option 2: Docker Compose (Full Stack)

Requires Docker and Docker Compose installed.

```bash
docker-compose up
```

**Access:**
- Application: http://localhost:7860
- API Docs: http://localhost:7860/docs

**Stop:**
```bash
docker-compose down
```

### Option 3: Production Server (Gunicorn + Uvicorn)

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### Option 4: Kubernetes Deployment

```bash
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl get pods
kubectl port-forward svc/pcos-api 8000:80
```

---

## API Documentation

### Authentication

**Register User:**
```bash
POST /auth/register
Content-Type: application/json

{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepassword123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Login:**
```bash
POST /auth/login
Content-Type: application/json

{
  "email": "jane@example.com",
  "password": "securepassword123"
}
```

### Health & Metrics

**System Health:**
```bash
GET /health

Response:
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2026-04-17T10:30:00Z",
  "version": "3.0.0"
}
```

**Model Metrics:**
```bash
GET /metrics

Response:
{
  "accuracy": 0.89,
  "precision": 0.85,
  "recall": 0.87,
  "f1_score": 0.86,
  "roc_auc": 0.92,
  "training_samples": 432,
  "test_samples": 109
}
```

### Risk Prediction

**Anonymous Prediction (No Auth Required):**
```bash
POST /predict
Content-Type: application/json

{
  "data": {
    "Age": 28,
    "Weight_kg": 65,
    "Height_cm": 165,
    "BMI": 23.9,
    "Cycle_length": 32,
    ...
  }
}

Response:
{
  "risk_percentage": 45.7,
  "risk_level": "moderate",
  "predictions": [0, 1],
  "probabilities": [0.54, 0.46]
}
```

**Authenticated Prediction (With DB Save & Recommendations):**
```bash
POST /predict/full
Authorization: Bearer <token>
Content-Type: application/json

{
  "data": { ... }
}

Response:
{
  "record_id": "uuid",
  "risk_percentage": 45.7,
  "risk_level": "moderate",
  "recommendations": [
    "Maintain regular exercise routine",
    "Balance carbohydrate intake",
    "Monitor weight regularly"
  ],
  "created_at": "2026-04-17T10:30:00Z"
}
```

### Health History

**Get Personal Health Records:**
```bash
GET /history
Authorization: Bearer <token>

Response:
[
  {
    "record_id": "uuid",
    "risk_percentage": 45.7,
    "created_at": "2026-04-17T10:30:00Z",
    "recommendations": [...]
  },
  ...
]
```

### Recommendations

**Get Lifestyle Recommendations:**
```bash
POST /recommend
Content-Type: application/json

{
  "risk_level": "moderate",
  "user_data": {
    "Age": 28,
    "Weight_kg": 65,
    ...
  }
}

Response:
{
  "recommendations": [
    "Maintain regular exercise routine",
    "Balance carbohydrate intake",
    "Monitor weight regularly"
  ]
}
```

### Menstrual Diary

**Log Diary Entry:**
```bash
POST /diary/entry
Authorization: Bearer <token>
Content-Type: application/json

{
  "entry_date": "2026-04-17",
  "period_status": "bleeding",
  "flow_level": "heavy",
  "symptoms": ["cramps", "fatigue"],
  "mood": "anxious",
  "notes": "Feeling tired today"
}

Response:
{
  "entry_id": "uuid",
  "insights": "Based on your diary entry, consider...",
  "created_at": "2026-04-17T10:30:00Z"
}
```

---

## Database Schema

### User Model

```sql
CREATE TABLE user (
  user_id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Health Record

```sql
CREATE TABLE health_record (
  record_id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY,
  age INTEGER,
  weight_kg FLOAT,
  height_cm FLOAT,
  bmi FLOAT,
  risk_percentage FLOAT,
  risk_level VARCHAR(20),
  recommendations TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Progress Record

```sql
CREATE TABLE progress_record (
  progress_id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY,
  previous_risk FLOAT,
  current_risk FLOAT,
  improvement_percentage FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Menstrual Record

```sql
CREATE TABLE menstrual_record (
  entry_id UUID PRIMARY KEY,
  user_id UUID FOREIGN KEY,
  entry_date DATE,
  period_status VARCHAR(50),
  flow_level VARCHAR(20),
  symptoms TEXT,
  mood VARCHAR(50),
  notes TEXT,
  insights TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:** Ensure virtual environment is activated and requirements installed:
```bash
# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Issue: "GEMINI_API_KEY not found"

**Solution:** Create `.env` file with your API key:
```env
GEMINI_API_KEY=your_key_here
```

Or set environment variable:
```bash
set GEMINI_API_KEY=your_key_here  # Windows
export GEMINI_API_KEY=your_key_here  # macOS/Linux
```

### Issue: "pcos_ml_model.pkl not found"

**Solution:** Train the model:
```bash
python _dev_backup/train_ml_model.py
```

Requires `PCOS_data_without_infertility.xlsx` in the working directory.

### Issue: "Address already in use" (port 7860)

**Solution:** Either:
1. Kill process using the port:
   ```bash
   netstat -ano | findstr :7860  # Windows
   # Then: taskkill /PID <PID> /F
   ```
2. Use different port:
   ```bash
   python -m uvicorn app.main:app --port 8001
   ```

### Issue: Database locked

**Solution:** Delete and recreate database:
```bash
rm herhealthai.db
# Restart the application - it will auto-create the database
```

### Issue: Authentication fails

**Verify:**
1. `.env` file contains `SECRET_KEY` and `ALGORITHM`
2. Database tables created (`user` table)
3. Check API docs for correct auth header format: `Authorization: Bearer <token>`

### Issue: Predictions return errors

**Check:**
1. All 25+ required input fields provided
2. Values within valid ranges (e.g., Age: 18-80, BMI: 15-50)
3. Model file (`pcos_ml_model.pkl`) exists and is valid
4. All 25 features properly mapped

---

## Performance Tuning

### For Development
```bash
# Single-threaded with reload
python -m uvicorn app.main:app --reload --port 7860
```

### For Production
```bash
# Multi-worker with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Database Optimization
- Add indexes on frequently queried columns (user_id, created_at)
- Archive old health records periodically
- Use connection pooling in production

---

## Security Checklist

- [ ] Change `SECRET_KEY` in `.env` to a secure random value
- [ ] Use strong passwords (enforce in frontend validation)
- [ ] Enable HTTPS in production (use reverse proxy like Nginx)
- [ ] Implement rate limiting (already enabled with slowapi)
- [ ] Store GEMINI_API_KEY securely (not in version control)
- [ ] Validate all user inputs (already done with Pydantic)
- [ ] Use environment-specific settings (dev vs production)
- [ ] Rotate API keys periodically
- [ ] Monitor access logs for suspicious activity

---

## Environment Variables Reference

| Variable | Default | Purpose | Required |
|----------|---------|---------|----------|
| `SECRET_KEY` | `herhealthai-super-secret-key-2026-pcos` | JWT signing key | No (has default) |
| `ALGORITHM` | `HS256` | JWT algorithm | No (has default) |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | Token expiration | No (has default) |
| `GEMINI_API_KEY` | `""` | Google Gemini API key | **YES** (for recommendations) |
| `FRONTEND_ORIGINS` | `*` | CORS allowed origins | No (allows all) |
| `DATABASE_URL` | `sqlite:///./herhealthai.db` | Database connection string | No (has SQLite default) |
| `LOG_LEVEL` | `INFO` | Logging level | No (has default) |

---

## Useful Commands

```bash
# Virtual environment
python -m venv venv              # Create venv
.\venv\Scripts\Activate.ps1      # Activate (Windows)
source venv/bin/activate         # Activate (macOS/Linux)
deactivate                       # Deactivate

# Installation
pip install -r requirements.txt  # Install dependencies
pip freeze > requirements.txt    # Update requirements
pip install -e .                 # Install in dev mode

# Running
python -m uvicorn app.main:app --reload --port 7860

# Testing
pytest test_backend.py           # Run tests
python scratch/inspect_db.py     # Inspect database

# Database
python _dev_backup/train_ml_model.py  # Retrain model

# Docker
docker build -t herhealthai .    # Build image
docker run -p 7860:7860 herhealthai  # Run container
docker-compose up                # Start with Docker Compose
```

---

## Project Links

- **Repository**: [GitHub Link]
- **API Documentation** (interactive): http://localhost:7860/docs
- **Alternative Docs**: http://localhost:7860/redoc
- **Issue Tracker**: GitHub Issues
- **License**: MIT

---

**Version**: 3.0.0  
**Last Updated**: April 17, 2026  
**Maintained By**: Development Team

