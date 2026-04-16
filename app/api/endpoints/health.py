from fastapi import APIRouter
from datetime import datetime
from app.ml.model import ModelStore

router = APIRouter()

@router.get('/health', tags=['System'])
def health_check():
    return {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'model_loaded': ModelStore.ML_MODEL is not None,
        'version': '3.0.0'
    }

@router.get('/metrics', tags=['System'])
def model_metrics():
    return {
        'model_name': ModelStore.MODEL_METRICS.get('model_name', 'Random Forest'),
        'accuracy':   round(float(ModelStore.MODEL_METRICS.get('accuracy', 0)) * 100, 2),
        'precision':  round(float(ModelStore.MODEL_METRICS.get('precision', 0)) * 100, 2),
        'recall':     round(float(ModelStore.MODEL_METRICS.get('recall', 0)) * 100, 2),
        'f1_score':   round(float(ModelStore.MODEL_METRICS.get('f1_score', 0)) * 100, 2),
        'roc_auc':    round(float(ModelStore.MODEL_METRICS.get('roc_auc', 0)) * 100, 2),
        'training_samples': ModelStore.MODEL_METRICS.get('training_samples', 432),
        'test_samples':     ModelStore.MODEL_METRICS.get('test_samples', 109),
    }
