import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.main import app
from continuous_learning.data_collector import fetch_unprocessed_feedback_data
from continuous_learning.config import CANDIDATE_METRICS_PATH

client = TestClient(app)

def test_full_pipeline():
    print("1. Testing Prediction Logging (Main Application)...")
    payload = {
        "dob": "1995-01-01",
        "weight": 85,
        "height": 165,
        "cycle_regular": 1,
        "weight_gain": 1,
        "pimples": 1
    }
    
    res = client.post("/predict", json=payload)
    if res.status_code != 200:
        print(f"Prediction failed: {res.text}")
        return
        
    result = res.json()
    req_id = result.get('request_id')
    print(f"  Prediction successful. Risk Percentage: {result.get('risk_percentage')}%")
    print(f"  Request ID captured: {req_id}")
    
    print("\n2. Testing Feedback Logging...")
    fb_payload = {
        "request_id": req_id,
        "diagnosis": "Yes" # Confirming condition
    }
    fb_res = client.post("/feedback", json=fb_payload)
    if fb_res.status_code != 200:
        print(f"Feedback failed: {fb_res.text}")
        return
        
    print(f"  Feedback logged. System responded: {fb_res.json()}")
    
    print("\n3. Testing Unprocessed Data Fetch...")
    unprocessed = fetch_unprocessed_feedback_data()
    print(f"  Unprocessed records found: {len(unprocessed)}")
    
    print("\n4. Triggering Manual Pipeline Execution...")
    from continuous_learning.scheduler import retraining_job
    
    # We remove previous artifacts for clean test
    if os.path.exists(CANDIDATE_METRICS_PATH):
        os.remove(CANDIDATE_METRICS_PATH)
        
    retraining_job()
    
    print("\n[SUCCESS] All Continuous Learning Framework Tests Completed in Main App!")

if __name__ == "__main__":
    test_full_pipeline()
