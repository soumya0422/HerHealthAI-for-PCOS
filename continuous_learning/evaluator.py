import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
from .config import CANDIDATE_METRICS_PATH

def evaluate_model(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except Exception:
        roc_auc = 0.0
        
    cm = confusion_matrix(y_test, y_pred).tolist()
    
    metrics = {
        "model_name": "Random Forest - Continuous Candidate",
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1_score": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": cm,
        "test_samples": len(y_test)
    }
    
    with open(CANDIDATE_METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Candidate Metrics: F1={f1:.4f}, Acc={acc:.4f}")
    return metrics
