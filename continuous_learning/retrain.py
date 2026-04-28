import pickle
from sklearn.ensemble import RandomForestClassifier
from .config import CANDIDATE_MODEL_PATH
from .preprocess import get_training_data, preprocess_for_training, load_production_artifacts

def train_candidate_model():
    print("Initiating retraining pipeline...")
    
    X_raw, y_raw, new_request_ids = get_training_data()
    print(f"Dataset assembled. Total shape: {X_raw.shape}")
    
    if len(new_request_ids) > 0:
        print(f"Learning from {len(new_request_ids)} new feedback entries.")
    else:
        print("No new feedback data. Training on original dataset.")
        
    encoders, scaler = load_production_artifacts()
    
    X_scaled, new_scaler = preprocess_for_training(X_raw, encoders, scaler)
    
    import pandas as pd
    y_raw = pd.to_numeric(y_raw, errors='coerce').fillna(0).astype(int)
    
    # Initialize Random Forest identical to original params
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    
    print("Fitting model...")
    model.fit(X_scaled, y_raw)
    print("Model fitted successfully.")
    
    # Save pre-scaling feature means for per-prediction key factor analysis
    import numpy as np
    numeric_means = X_raw.apply(lambda col: pd.to_numeric(col, errors='coerce')).mean()
    feature_means = [float(numeric_means.get(c, 0.0)) if not pd.isna(numeric_means.get(c, 0.0)) else 0.0 for c in X_raw.columns]

    model_package = {
        'model': model,
        'scaler': new_scaler,
        'label_encoders': encoders,
        'feature_names': list(X_raw.columns),
        'categorical_cols': list(encoders.keys()) if encoders else [],
        'feature_means': feature_means,
    }
    
    with open(CANDIDATE_MODEL_PATH, 'wb') as f:
        pickle.dump(model_package, f)
        
    print(f"Candidate model saved to {CANDIDATE_MODEL_PATH}")
    
    return X_scaled, y_raw, new_request_ids, model

if __name__ == "__main__":
    train_candidate_model()
