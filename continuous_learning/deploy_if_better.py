import json
import os
import shutil
import datetime
from .config import (
    PRODUCTION_MODEL_PATH, 
    PRODUCTION_METRICS_PATH, 
    CANDIDATE_MODEL_PATH, 
    CANDIDATE_METRICS_PATH, 
    BACKUP_DIR, 
    IMPROVEMENT_THRESHOLD
)
from .data_collector import mark_processed

def deploy_model_if_improved(new_request_ids):
    if not os.path.exists(CANDIDATE_METRICS_PATH) or not os.path.exists(CANDIDATE_MODEL_PATH):
        print("Candidate artifacts missing. Aborting deployment.")
        return False
        
    with open(CANDIDATE_METRICS_PATH, 'r') as f:
        candidate_metrics = json.load(f)
        
    candidate_f1 = candidate_metrics.get('f1_score', 0)
    
    prod_f1 = 0
    if os.path.exists(PRODUCTION_METRICS_PATH):
        try:
            with open(PRODUCTION_METRICS_PATH, 'r') as f:
                prod_metrics = json.load(f)
            prod_f1 = prod_metrics.get('f1_score', 0)
        except Exception:
            pass
            
    print(f"Comparing Models: Production F1={prod_f1:.4f} vs Candidate F1={candidate_f1:.4f}")
    
    if (candidate_f1 - prod_f1) >= IMPROVEMENT_THRESHOLD:
        print(f"Candidate model is better by {(candidate_f1 - prod_f1):.4f}. Deploying...")
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(PRODUCTION_MODEL_PATH):
            shutil.copy(PRODUCTION_MODEL_PATH, os.path.join(BACKUP_DIR, f"model_backup_{timestamp}.pkl"))
        if os.path.exists(PRODUCTION_METRICS_PATH):
            shutil.copy(PRODUCTION_METRICS_PATH, os.path.join(BACKUP_DIR, f"metrics_backup_{timestamp}.json"))
            
        shutil.copy(CANDIDATE_MODEL_PATH, PRODUCTION_MODEL_PATH)
        shutil.copy(CANDIDATE_METRICS_PATH, PRODUCTION_METRICS_PATH)
        
        print("Deployment successful.")
        
        mark_processed(new_request_ids)
        return True
    else:
        print("Candidate model did not improve baseline significantly. Discarding.")
        return False

if __name__ == "__main__":
    deploy_model_if_improved([])
