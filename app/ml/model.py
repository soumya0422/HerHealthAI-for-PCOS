import json
import pickle
import logging

logger = logging.getLogger(__name__)

from continuous_learning.config import PRODUCTION_MODEL_PATH as MODEL_PATH
from continuous_learning.config import PRODUCTION_METRICS_PATH as METRICS_PATH

class ModelStore:
    ML_MODEL  = None
    SCALER    = None
    ENCODERS  = {}
    X_COLUMNS = []
    CATEGORICAL_COLS = []
    FEATURE_IMPORTANCE = []
    FEATURE_MEANS = None        # Training-set feature means for per-prediction analysis
    MODEL_METRICS = {}

def load_ml_model():
    try:
        with open(MODEL_PATH, 'rb') as f:
            data = pickle.load(f)
        ModelStore.ML_MODEL         = data['model']
        ModelStore.SCALER           = data['scaler']
        ModelStore.ENCODERS         = data.get('label_encoders', {})
        ModelStore.X_COLUMNS        = data.get('X_columns', data.get('feature_names', []))
        ModelStore.CATEGORICAL_COLS = data.get('categorical_cols', [])
        ModelStore.FEATURE_IMPORTANCE = data.get('feature_importance', [])
        ModelStore.FEATURE_MEANS    = data.get('feature_means', None)
        logger.info(f"ML model loaded: {type(ModelStore.ML_MODEL).__name__}, {len(ModelStore.X_COLUMNS)} features")
    except Exception as e:
        logger.error(f"Failed to load ML model: {e}")

def load_metrics():
    try:
        with open(METRICS_PATH, 'r') as f:
            ModelStore.MODEL_METRICS = json.load(f)
        logger.info(f"Model metrics loaded: accuracy={ModelStore.MODEL_METRICS.get('accuracy', 0):.4f}")
    except Exception as e:
        logger.warning(f"Could not load metrics: {e}")
        ModelStore.MODEL_METRICS = {}

load_ml_model()
load_metrics()
