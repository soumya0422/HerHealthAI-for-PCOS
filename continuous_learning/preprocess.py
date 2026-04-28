import pandas as pd
import numpy as np
import json
import pickle
import os
from .config import ORIGINAL_DATA_PATH, PRODUCTION_MODEL_PATH, EXPECTED_FEATURES
from .data_collector import fetch_unprocessed_feedback_data

def load_production_artifacts():
    try:
        with open(PRODUCTION_MODEL_PATH, 'rb') as f:
            data = pickle.load(f)
        return data.get('label_encoders', {}), data.get('scaler')
    except Exception as e:
        print(f"Failed to load production artifacts: {e}")
        return {}, None

def get_training_data():
    """
    Loads original data and merges with any new feedback data.
    Returns: X (DataFrame), y (Series), new_request_ids (List)
    """
    try:
        df_original = pd.read_excel(ORIGINAL_DATA_PATH, sheet_name='Full_new')
    except Exception as e:
        raise RuntimeError(f"Could not load original dataset: {e}")
        
    X_orig = df_original.copy()
    y_orig = df_original['PCOS (Y/N)'].copy()
    
    feedback_entries = fetch_unprocessed_feedback_data()
    new_request_ids = [entry['request_id'] for entry in feedback_entries]
    
    new_rows = []
    new_labels = []
    
    for entry in feedback_entries:
        try:
            features = json.loads(entry['features_json'])
            new_rows.append(features)
            label = 1 if str(entry['diagnosis_feedback']).lower() in ['yes', 'y', '1', 'true'] else 0
            new_labels.append(label)
        except Exception:
            pass
            
    if new_rows:
        df_new = pd.DataFrame(new_rows)
        y_new = pd.Series(new_labels)
        
        for col in EXPECTED_FEATURES:
            if col not in df_new.columns:
                df_new[col] = 0.0
                
        df_new = df_new[EXPECTED_FEATURES]
        
        for col in EXPECTED_FEATURES:
            if col not in X_orig.columns:
                X_orig[col] = 0.0
        X_orig = X_orig[EXPECTED_FEATURES]
        
        X_final = pd.concat([X_orig, df_new], ignore_index=True)
        y_final = pd.concat([y_orig, y_new], ignore_index=True)
    else:
        for col in EXPECTED_FEATURES:
            if col not in X_orig.columns:
                X_orig[col] = 0.0
        X_final = X_orig[EXPECTED_FEATURES]
        y_final = y_orig
        
    return X_final, y_final, new_request_ids

def preprocess_for_training(X, encoders=None, scaler=None):
    """Cleans/scales data and handles label encoding."""
    X_processed = X.copy()
    X_processed.fillna(0, inplace=True)
    
    if encoders:
        for col, encoder in encoders.items():
            if col in X_processed.columns:
                try:
                    X_processed[col] = X_processed[col].astype(str)
                    classes = list(encoder.classes_)
                    X_processed[col] = X_processed[col].apply(
                        lambda x: encoder.transform([x])[0] if x in classes else 0
                    )
                except Exception as e:
                    print(f"Encoding error on {col}: {e}")
                    X_processed[col] = 0
                    
    for col in X_processed.columns:
        X_processed[col] = pd.to_numeric(X_processed[col], errors='coerce').fillna(0)
        
    if scaler:
        X_scaled = scaler.fit_transform(X_processed)
        return X_scaled, scaler
    else:
        from sklearn.preprocessing import StandardScaler
        new_scaler = StandardScaler()
        X_scaled = new_scaler.fit_transform(X_processed)
        return X_scaled, new_scaler
