import sqlite3
import json
import uuid
import os
from datetime import datetime
from threading import Lock
from .config import DB_PATH

db_lock = Lock()

def get_connection():
    # Make sure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS predictions (
                    request_id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    features_json TEXT,
                    prediction_prob REAL,
                    prediction_level TEXT,
                    diagnosis_feedback TEXT,
                    processed INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

init_db()

def log_prediction(req_id: str, features: dict, prediction_prob: float, prediction_level: str) -> str:
    """Logs the incoming prediction API call to SQLite. Returns unique string ID."""
    timestamp = datetime.utcnow().isoformat()
    # Normalize features to be JSON serializable
    clean_features = {k: v for k, v in features.items() if v is not None}
    features_json = json.dumps(clean_features)
    
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO predictions (request_id, timestamp, features_json, prediction_prob, prediction_level)
                VALUES (?, ?, ?, ?, ?)
            ''', (req_id, timestamp, features_json, prediction_prob, prediction_level))
            conn.commit()
            
    return req_id

def log_feedback(request_id: str, diagnosis: str) -> bool:
    """Logs the confirmed diagnosis later. diagnosis should be 'Yes' or 'No'."""
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE predictions SET diagnosis_feedback = ? WHERE request_id = ?', 
                           (diagnosis, request_id))
            conn.commit()
            return cursor.rowcount > 0

def fetch_unprocessed_feedback_data():
    """Fetches records that have been mapped to actual feedback but haven't been used in a pipeline."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE diagnosis_feedback IS NOT NULL 
            AND processed = 0
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
def mark_processed(request_ids):
    """Marks feedback data as processed to prevent duplicate training weights."""
    if not request_ids:
        return
    with db_lock:
        with get_connection() as conn:
            cursor = conn.cursor()
            seq = ','.join(['?']*len(request_ids))
            cursor.execute(f'UPDATE predictions SET processed = 1 WHERE request_id IN ({seq})', request_ids)
            conn.commit()
