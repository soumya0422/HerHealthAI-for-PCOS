import schedule
import time
import threading
from .retrain import train_candidate_model
from .evaluator import evaluate_model
from .deploy_if_better import deploy_model_if_improved
from .data_collector import fetch_unprocessed_feedback_data

def retraining_job():
    print("--- Starting Scheduled Retraining Job ---")
    feedback = fetch_unprocessed_feedback_data()
    if not feedback:
        print("No new feedback data to learn from. Skipping retraining.")
        return
        
    try:
        X_scaled, y_raw, new_request_ids, model = train_candidate_model()
        evaluate_model(model, X_scaled, y_raw)
        deploy_model_if_improved(new_request_ids)
    except Exception as e:
        print(f"Retraining job failed: {e}")

def run_scheduler_bg():
    schedule.every(7).days.do(retraining_job)
    print("Continuous Learning Scheduler background thread started. Checking every hour.")
    while True:
        schedule.run_pending()
        time.sleep(3600)

def start_scheduler():
    t = threading.Thread(target=run_scheduler_bg, daemon=True)
    t.start()
