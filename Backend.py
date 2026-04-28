import os
import pickle
import math
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from continuous_learning.data_collector import log_prediction, log_feedback
from continuous_learning.scheduler import start_scheduler

try:
    start_scheduler()
except Exception as e:
    print("Warning: Scheduler failed to start:", e)

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ML-based PCOS Risk Prediction API
# This backend uses a trained Random Forest model trained on 541 PCOS patient records
# with 41 medical features, achieving 91.74% accuracy.

FRONTEND_ORIGINS = os.environ.get('FRONTEND_ORIGINS', '*')

app = FastAPI(title='PCOS Risk API (ML-Based)')

if FRONTEND_ORIGINS.strip() == '*' or FRONTEND_ORIGINS == '':
    origins = ["*"]
else:
    origins = [o.strip() for o in FRONTEND_ORIGINS.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load pre-trained ML model
try:
    model_path = os.path.join(os.path.dirname(__file__), 'pcos_ml_model.pkl')
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    TRAINED_MODEL = model_data['model']
    SCALER = model_data['scaler']
    LABEL_ENCODERS = model_data['label_encoders']
    FEATURE_NAMES = model_data['feature_names']
    CATEGORICAL_COLS = model_data['categorical_cols']
    print(f"[OK] ML Model loaded successfully. Features: {len(FEATURE_NAMES)}")
except Exception as e:
    print(f"[WARNING] Could not load ML model. Falling back to heuristic. Error: {e}")
    TRAINED_MODEL = None
    SCALER = None
    LABEL_ENCODERS = {}
    FEATURE_NAMES = []


class PredictRequest(BaseModel):
    data: Dict[str, Optional[float]]
    targets: Optional[list] = None


def _sigmoid(x: float) -> float:
    """Apply sigmoid function to normalize score to [0, 1]"""
    try:
        return 1 / (1 + math.exp(-x))
    except (ValueError, OverflowError):
        return 1.0 if x > 0 else 0.0


# ---------------------------------------------------------------------------
# Key-Factor Configuration (replaces all hardcoded magic numbers)
# Each rule describes one clinical factor that feeds the heuristic fallback.
#
# Fields:
#   input_keys    – ordered list of dict keys to try when reading from `row`
#   baseline      – clinically normal reference value
#   scale         – weight applied to (|value - baseline| / normalizer)
#   normalizer    – divisor that converts the deviation into a [0..1] range
#   direction     – 'above'  → risk rises when value > baseline
#                   'below'  → risk rises when value < baseline
#                   'both'   → deviation in either direction increases risk
#   label         – human-readable display name returned in top_explanations
#   unit          – display unit appended to the value string
# ---------------------------------------------------------------------------
HEURISTIC_RULES: list = [
    {
        "label": "BMI",
        "input_keys": ["BMI"],
        "baseline": 23.0,
        "scale": 0.08,
        "normalizer": 1.0,
        "direction": "above",
        "unit": "",
    },
    {
        "label": "Cycle Irregularity",
        "input_keys": ["Cycle_length", "Cycle length(days)"],
        "baseline": 28.0,
        "scale": 0.6,
        "normalizer": 14.0,
        "direction": "both",
        "unit": " days",
    },
    {
        "label": "Pulse Rate",
        "input_keys": ["Pulse rate(bpm) ", "Pulse rate(bpm)", "Pulse"],
        "baseline": 70.0,
        "scale": 0.01,
        "normalizer": 1.0,
        "direction": "above",
        "unit": " bpm",
    },
    {
        "label": "RBS Level",
        "input_keys": ["RBS(mg/dl)", "RBS"],
        "baseline": 90.0,
        "scale": 0.002,
        "normalizer": 1.0,
        "direction": "above",
        "unit": " mg/dl",
    },
    {
        "label": "AMH",
        "input_keys": ["AMH(ng/mL)", "AMH"],
        "baseline": 3.5,
        "scale": 0.15,
        "normalizer": 3.5,
        "direction": "above",
        "unit": " ng/mL",
    },
    {
        "label": "LH/FSH Ratio",
        "input_keys": ["FSH/LH"],
        "baseline": 1.0,
        "scale": 0.12,
        "normalizer": 1.0,
        "direction": "above",
        "unit": "",
    },
    {
        "label": "Follicle Count (Left)",
        "input_keys": ["Follicle No. (L)"],
        "baseline": 10.0,
        "scale": 0.05,
        "normalizer": 1.0,
        "direction": "above",
        "unit": "",
    },
    {
        "label": "Follicle Count (Right)",
        "input_keys": ["Follicle No. (R)"],
        "baseline": 10.0,
        "scale": 0.05,
        "normalizer": 1.0,
        "direction": "above",
        "unit": "",
    },
]


def ml_risk_prediction(row: Dict[str, Optional[float]]) -> Dict[str, Any]:
    """
    Predict PCOS risk using trained ML model.
    
    Features used (in order):
    Age, Weight, Height, BMI, Pulse rate, RR, Hb, Cycle status, Cycle length,
    Marriage status, Beta-HCG (I & II), FSH, LH, FSH/LH, Hip, Waist, Waist:Hip,
    TSH, AMH, PRL, Vit D3, PRG, RBS, Weight gain, Hair growth, Skin darkening,
    Hair loss, Pimples, Fast food, Exercise, BP Systolic, BP Diastolic,
    Follicle No. (L), Follicle No. (R), Avg F size (L), Avg F size (R), Endometrium
    """
    try:
        # Create DataFrame with all required features
        input_data = pd.DataFrame([row])
        
        # Prepare features in the same order as training
        X_input = pd.DataFrame(index=[0])
        
        # Add numeric columns
        numeric_cols = FEATURE_NAMES  # Use original feature names from training
        
        for col in numeric_cols:
            if col in input_data.columns:
                X_input[col] = input_data[col].values
            else:
                # Try alternative column names
                alt_names = {
                    'Age (yrs)': ['Age', 'age'],
                    'Weight (Kg)': ['Weight'],
                    'Height(Cm) ': ['Height', 'Height(Cm)'],
                    'Pulse rate(bpm) ': ['Pulse', 'Pulse rate(bpm)'],
                    'RBS(mg/dl)': ['RBS', 'RBS (mg/dl)'],
                }
                
                found = False
                for alt_col in alt_names.get(col, []):
                    if alt_col in input_data.columns:
                        X_input[col] = input_data[alt_col].values
                        found = True
                        break
                
                if not found:
                    # Fill missing with 0 or median proxy
                    X_input[col] = 0.0
        
        # Encode categorical features
        for col in CATEGORICAL_COLS:
            if col in X_input.columns and col in LABEL_ENCODERS:
                try:
                    X_input[col] = LABEL_ENCODERS[col].transform(X_input[col].astype(str))
                except:
                    X_input[col] = 0
        
        # Scale features
        X_scaled = SCALER.transform(X_input)
        
        # Get prediction
        prob = float(TRAINED_MODEL.predict_proba(X_scaled)[0, 1])
        
        # -----------------------------------------------------------------------
        # Compute INPUT-WEIGHTED key factors
        # Instead of returning raw global importances (which are the same for
        # every patient), we weight each feature's importance by the magnitude
        # of the patient's *scaled* value, producing a per-prediction score
        # that reflects what actually drove THIS result.
        # -----------------------------------------------------------------------
        if hasattr(TRAINED_MODEL, 'feature_importances_'):
            feature_importance = TRAINED_MODEL.feature_importances_
            scaled_values = X_scaled[0]  # 1-D array of standardised values

            # Per-feature contribution = global_importance × |scaled_value|
            per_input_scores = feature_importance * np.abs(scaled_values)

            top_indices = np.argsort(per_input_scores)[::-1][:5]
            top_explanations = []

            for idx in top_indices:
                if idx < len(numeric_cols):
                    feature_name = numeric_cols[idx]
                    raw_value = X_input[feature_name].values[0] if feature_name in X_input.columns else 0
                    top_explanations.append({
                        'feature': feature_name,
                        'contribution': float(per_input_scores[idx]),
                        'value': f'{raw_value:.2f}'
                    })
        else:
            top_explanations = []
        
        bmi = None
        if 'BMI' in X_input.columns:
            bmi = float(X_input['BMI'].values[0])
        
        return {
            'prob': prob,
            'bmi': bmi,
            'top_explanations': top_explanations,
            'model_type': 'ML-Random Forest'
        }
    
    except Exception as e:
        print(f"ML prediction error: {e}")
        # Fallback to heuristic if ML fails
        return heuristic_risk_score(row)


def _read_rule_value(row: Dict[str, Optional[float]], keys: list) -> Optional[float]:
    """Try each key in order and return the first non-None numeric value found."""
    for key in keys:
        raw = row.get(key)
        if raw is not None:
            try:
                return float(raw)
            except (ValueError, TypeError):
                continue
    return None


def heuristic_risk_score(row: Dict[str, Optional[float]]) -> Dict[str, Any]:
    """
    Fallback: Compute PCOS risk score driven by HEURISTIC_RULES config.
    Used only if ML model is not available or fails.
    All weights, baselines, and thresholds live in HEURISTIC_RULES above —
    nothing is hardcoded inside this function.
    """
    # Derive BMI if not directly supplied
    bmi: Optional[float] = _read_rule_value(row, ["BMI"])
    if bmi is None:
        weight = _read_rule_value(row, ["Weight (Kg)", "Weight"])
        height = _read_rule_value(row, ["Height(Cm) ", "Height(Cm)", "Height"])
        if weight and height and height > 0:
            try:
                bmi = weight / ((height / 100) ** 2)
            except Exception:
                bmi = None

    # Inject derived BMI back so the BMI rule can read it
    effective_row = dict(row)
    if bmi is not None:
        effective_row["BMI"] = bmi

    score = 0.0
    contributions: list = []

    for rule in HEURISTIC_RULES:
        value = _read_rule_value(effective_row, rule["input_keys"])
        if value is None:
            continue

        baseline: float = rule["baseline"]
        scale: float = rule["scale"]
        normalizer: float = rule["normalizer"]
        direction: str = rule["direction"]

        if direction == "above":
            deviation = max(0.0, value - baseline)
        elif direction == "below":
            deviation = max(0.0, baseline - value)
        else:  # "both"
            deviation = abs(value - baseline)

        contribution = (deviation / normalizer) * scale
        if contribution > 0:
            score += contribution
            fmt_value = f"{value:.1f}{rule['unit']}"
            contributions.append((rule["label"], contribution, fmt_value))

    prob = float(_sigmoid(score))

    contrib_sorted = sorted(contributions, key=lambda x: -abs(x[1]))[:5]
    top_explanations = [
        {"feature": name, "contribution": float(val), "value": desc}
        for name, val, desc in contrib_sorted
    ]

    return {"prob": prob, "bmi": bmi, "top_explanations": top_explanations, "model_type": "Heuristic-Fallback"}


def get_level(prob: float) -> str:
    """Classify risk level based on probability"""
    p = prob * 100
    if p < 30:
        return 'Low'
    elif p < 70:
        return 'Moderate'
    else:
        return 'High'


@app.get('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'time': datetime.utcnow().isoformat()}


@app.post('/predict')
def api_predict(req: PredictRequest, background_tasks: BackgroundTasks):
    """
    Predict PCOS risk for given patient data.
    Uses ML model if available, falls back to heuristic rules.
    Returns risk percentage, level, and top contributing factors.
    """
    try:
        data = req.data or {}
        targets = req.targets or ['PCOS']
        out = {}
        
        for t in targets:
            # Use ML model if available
            if TRAINED_MODEL is not None:
                res = ml_risk_prediction(data)
            else:
                res = heuristic_risk_score(data)
            
            prob = res['prob']
            pct = round(prob * 100, 2)
            entry = {
                'risk_percentage': pct,
                'risk_level': get_level(prob),
                'top_explanations': res['top_explanations'],
                'model_type': res.get('model_type', 'Unknown')
            }
            if res.get('bmi') is not None:
                entry['BMI'] = round(res['bmi'], 2)
            
            req_id = str(uuid.uuid4())
            background_tasks.add_task(log_prediction, req_id, data, prob, get_level(prob))
            entry['request_id'] = req_id
                
            out[t] = entry
        
        # if single target requested, return single-object for compatibility
        if len(targets) == 1:
            return out[targets[0]]
        return out
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction error: {str(e)}")


@app.post('/recommend')
def api_recommend(req: PredictRequest):
    """Provide health recommendations based on patient data"""
    try:
        data = req.data or {}
        recs = []
        
        # BMI-based recommendation
        weight = float(data.get('Weight (Kg)', 0) or 0)
        height = float(data.get('Height(Cm)', 0) or 0)
        if weight > 0 and height > 0:
            bmi = weight / ((height / 100) ** 2)
            if bmi > 25:
                recs.append('Consider a weight management plan and consult a nutritionist')
        
        # Cycle regularity recommendation
        cycle = data.get('Cycle_length') or data.get('Cycle length(days)')
        try:
            if cycle and abs(float(cycle) - 28) > 7:
                recs.append('Consult gynecologist for cycle irregularity evaluation')
        except Exception:
            pass
        
        # Blood sugar recommendation
        rbs = float(data.get('RBS(mg/dl)', data.get('RBS', 0)) or 0)
        if rbs > 110:
            recs.append('Monitor blood sugar levels; consider dietary adjustments')
        
        if not recs:
            recs.append('Maintain healthy diet, regular exercise, and sleep hygiene')
        
        return {'recommendations': recs}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Recommendation error: {str(e)}")


class FeedbackRequest(BaseModel):
    request_id: str
    diagnosis: str

@app.post('/feedback')
def api_feedback(req: FeedbackRequest):
    """Stores verified clinical outcome for a past prediction to trigger continuous learning."""
    success = log_feedback(req.request_id, req.diagnosis)
    if success:
        return {"status": "success", "message": "Feedback recorded."}
    return {"status": "error", "message": "Request ID not found or error occurred."}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
