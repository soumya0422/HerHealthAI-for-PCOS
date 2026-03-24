import os
import math
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import numpy as np

# Minimal, robust backend so Streamlit frontend works immediately.
# This uses a simple heuristic scorer (no ML model) so `/predict` returns
# percentage risk and explanations without requiring dataset or training.

FRONTEND_ORIGINS = os.environ.get('FRONTEND_ORIGINS', '*')

app = FastAPI(title='PCOS Risk API (Heuristic)')

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


class PredictRequest(BaseModel):
    data: Dict[str, Optional[float]]
    targets: Optional[list] = None


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def heuristic_risk_score(row: Dict[str, Optional[float]]) -> Dict[str, Any]:
    # Extract features with reasonable defaults
    weight = float(row.get('Weight', row.get('weight', np.nan) or 0) or 0)
    height = float(row.get('Height', row.get('height', np.nan) or 0) or 0)
    bmi = None
    if weight > 0 and height > 0:
        try:
            bmi = weight / ((height / 100) ** 2)
        except Exception:
            bmi = None

    cycle = row.get('Cycle_length') or row.get('cycle_length') or row.get('cyclelength')
    cycle_val = None
    try:
        cycle_val = float(cycle) if cycle is not None else None
    except Exception:
        cycle_val = None

    pulse = row.get('Pulse rate(bpm)') or row.get('pulse') or row.get('Pulse') or 0
    try:
        pulse = float(pulse or 0)
    except Exception:
        pulse = 0

    rbs = row.get('RBS') or row.get('RBS(mg/dl)') or row.get('rbs') or 0
    try:
        rbs = float(rbs or 0)
    except Exception:
        rbs = 0

    # Build a simple linear score
    score = 0.0
    contributions = []

    if bmi is not None:
        c = max(0.0, (bmi - 23.0)) * 0.08
        score += c
        contributions.append(('BMI', c))

    if cycle_val is not None:
        c = (abs(cycle_val - 28) / 14.0) * 0.6
        score += c
        contributions.append(('CycleIrregularity', c))

    if pulse:
        c = max(0.0, (pulse - 70)) * 0.01
        score += c
        contributions.append(('Pulse', c))

    if rbs:
        c = max(0.0, (rbs - 90)) * 0.002
        score += c
        contributions.append(('RBS', c))

    # Normalize through sigmoid to [0,1]
    prob = float(_sigmoid(score))

    # Prepare top contributors by absolute contribution
    contrib_sorted = sorted(contributions, key=lambda x: -abs(x[1]))[:5]
    top_explanations = [{'feature': k, 'contribution': float(v)} for k, v in contrib_sorted]

    return {'prob': prob, 'bmi': bmi, 'top_explanations': top_explanations}


def get_level(prob: float) -> str:
    p = prob * 100
    if p < 30:
        return 'Low'
    elif p < 70:
        return 'Moderate'
    else:
        return 'High'


@app.get('/health')
def health():
    return {'status': 'ok', 'time': datetime.utcnow().isoformat()}


@app.post('/train')
def api_train(background: BackgroundTasks, data_path: Optional[str] = None, sheet_name: Optional[str] = None):
    # placeholder: no-op training in heuristic backend
    def _task(p, s):
        # simulate short task
        import time as _t
        _t.sleep(1)

    background.add_task(_task, data_path, sheet_name)
    return {'status': 'training_started', 'note': 'heuristic backend - no model trained'}


@app.post('/predict')
def api_predict(req: PredictRequest):
    data = req.data or {}
    targets = req.targets or ['PCOS']
    out = {}
    for t in targets:
        res = heuristic_risk_score(data)
        prob = res['prob']
        pct = round(prob * 100, 2)
        entry = {'risk_percentage': pct, 'risk_level': get_level(prob), 'top_explanations': res['top_explanations']}
        if res['bmi'] is not None:
            entry['BMI'] = round(res['bmi'], 2)
        out[t] = entry
    # if single target requested, return single-object for compatibility
    if len(targets) == 1:
        return out[targets[0]]
    return out


@app.post('/recommend')
def api_recommend(req: PredictRequest):
    data = req.data or {}
    recs = []
    bmi = data.get('BMI') or data.get('Weight') and data.get('Height')
    if isinstance(bmi, (int, float)):
        if bmi > 25:
            recs.append('Consider a weight management plan and consult a nutritionist')

    cycle = data.get('Cycle_length') or data.get('cycle_length')
    try:
        if cycle and abs(float(cycle) - 28) > 7:
            recs.append('Consult gynecologist for cycle irregularity evaluation')
    except Exception:
        pass

    if not recs:
        recs.append('Maintain healthy diet, regular exercise, and sleep hygiene')
    return {'recommendations': recs}


if __name__ == '__main__':
    import uvicorn
    from datetime import datetime
    print('Starting heuristic PCOS backend on http://0.0.0.0:8000')
    uvicorn.run('Backend:app', host='0.0.0.0', port=8000, reload=True)
