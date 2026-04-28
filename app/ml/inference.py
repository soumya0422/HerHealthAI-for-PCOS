import json
import logging
from typing import Dict, Any
import numpy as np
from app.ml.model import ModelStore
from app.config import settings

logger = logging.getLogger(__name__)

FEATURE_DEFAULTS = {
    'I   beta-HCG(mIU/mL)': 1.0,
    'II    beta-HCG(mIU/mL)': 1.0,
    'FSH(mIU/mL)': 6.5,
    'LH(mIU/mL)': 7.0,
    'FSH/LH': 0.93,
    'Follicle No. (L)': 5.0,
    'Follicle No. (R)': 5.0,
    'Avg. F size (L) (mm)': 18.0,
    'Avg. F size (R) (mm)': 18.0,
    'Endometrium (mm)': 9.0,
    'PRG(ng/mL)': 1.5,
    'No. of abortions': 0.0,
    'Pregnant(Y/N)': 0,
    'Marraige Status (Yrs)': 2.0,
}

def build_feature_vector(user_input: Dict[str, Any]) -> np.ndarray:
    if not ModelStore.X_COLUMNS:
        raise RuntimeError("Model feature columns not loaded")

    row = {}
    for col in ModelStore.X_COLUMNS:
        row[col] = FEATURE_DEFAULTS.get(col, 0.0)

    field_map = {
        'age':            ['Age (yrs)', 'Age'],
        'weight':         ['Weight (Kg)', 'Weight'],
        'height':         ['Height(Cm)', 'Height'],
        'bmi':            ['BMI'],
        'pulse':          ['Pulse rate(bpm) ', 'Pulse rate(bpm)', 'Pulse'],
        'rr':             ['RR (breaths/min)', 'RR'],
        'hb':             ['Hb(g/dl)', 'Hb'],
        'cycle_regular':  ['Cycle(R/I)'],
        'cycle_length':   ['Cycle length(days)', 'Cycle_length'],
        'waist':          ['Waist(inch)', 'Waist'],
        'hip':            ['Hip(inch)', 'Hip'],
        'waist_hip':      ['Waist:Hip Ratio'],
        'tsh':            ['TSH (mIU/L)', 'TSH'],
        'amh':            ['AMH(ng/mL)', 'AMH'],
        'prl':            ['PRL(ng/mL)', 'PRL'],
        'vitd':           ['Vit D3 (ng/mL)', 'Vit D3'],
        'rbs':            ['RBS(mg/dl)', 'RBS'],
        'bp_systolic':    ['BP _Systolic (mmHg)', 'BP_Systolic'],
        'bp_diastolic':   ['BP _Diastolic (mmHg)', 'BP_Diastolic'],
        'weight_gain':    ['Weight gain(Y/N)', 'weight_gain'],
        'hair_growth':    ['hair growth(Y/N)', 'hair_growth'],
        'skin_darkening': ['Skin darkening (Y/N)', 'skin_darkening'],
        'hair_loss':      ['Hair loss(Y/N)', 'hair_loss'],
        'pimples':        ['Pimples(Y/N)', 'pimples'],
        'fast_food':      ['Fast food (Y/N)', 'fast_food'],
        'exercise':       ['Reg.Exercise(Y/N)', 'exercise'],
        'fsh':            ['FSH(mIU/mL)', 'FSH'],
        'lh':             ['LH(mIU/mL)', 'LH'],
        'fsh_lh':         ['FSH/LH'],
        'marriage_years': ['Marraige Status (Yrs)'],
    }

    for ui_key, col_variants in field_map.items():
        val = user_input.get(ui_key)
        if val is None:
            continue
        for col in col_variants:
            if col in ModelStore.X_COLUMNS:
                try:
                    row[col] = float(val)
                except (ValueError, TypeError):
                    pass
                break

    bmi_col = next((c for c in ['BMI'] if c in ModelStore.X_COLUMNS), None)
    if bmi_col and row.get(bmi_col, 0) == 0:
        w = row.get('Weight (Kg)', 0) or row.get('Weight', 0)
        h = row.get('Height(Cm)', 0) or row.get('Height', 0)
        if w > 0 and h > 0:
            try:
                row[bmi_col] = round(w / ((h / 100) ** 2), 2)
            except Exception:
                pass

    wh_col = next((c for c in ['Waist:Hip Ratio'] if c in ModelStore.X_COLUMNS), None)
    if wh_col:
        waist_col = next((c for c in ['Waist(inch)'] if c in ModelStore.X_COLUMNS), None)
        hip_col   = next((c for c in ['Hip(inch)'] if c in ModelStore.X_COLUMNS), None)
        if waist_col and hip_col:
            w_val = row.get(waist_col, 0)
            h_val = row.get(hip_col, 0)
            if h_val > 0:
                row[wh_col] = round(w_val / h_val, 4)

    if 'FSH/LH' in ModelStore.X_COLUMNS:
        fsh_val = row.get('FSH(mIU/mL)', 0)
        lh_val  = row.get('LH(mIU/mL)', 1)
        if lh_val and lh_val > 0:
            row['FSH/LH'] = round(fsh_val / lh_val, 4)
            # Clinical mapping: extremely high LH/FSH correlates directly to polycystic morphology
            if row['FSH/LH'] < 0.5 and row.get('Cycle(R/I)', 0) == 0:
                row['Follicle No. (L)'] = 16.0
                row['Follicle No. (R)'] = 16.0

    for col in ModelStore.CATEGORICAL_COLS:
        if col in ModelStore.ENCODERS and col in ModelStore.X_COLUMNS:
            raw = row.get(col, 0)
            try:
                enc_val = ModelStore.ENCODERS[col].transform([str(int(raw))])[0]
                row[col] = int(enc_val)
            except Exception:
                row[col] = 0

    feature_vec = np.array([row.get(col, 0.0) for col in ModelStore.X_COLUMNS], dtype=float)
    return feature_vec

FEATURE_LABELS = {
    'Age (yrs)':              'Age',
    'Weight (Kg)':            'Weight',
    'Height(Cm)':             'Height',
    'Height(Cm) ':            'Height',
    'BMI':                    'BMI',
    'Pulse rate(bpm) ':       'Pulse Rate',
    'Pulse rate(bpm)':        'Pulse Rate',
    'RR (breaths/min)':       'Breathing Rate',
    'Hb(g/dl)':               'Hemoglobin',
    'Cycle(R/I)':             'Cycle Regularity',
    'Cycle length(days)':     'Cycle Length',
    'Marraige Status (Yrs)':  'Marriage Years',
    'Pregnant(Y/N)':          'Pregnancy Status',
    'No. of aborptions':      'No. of Abortions',
    'No. of abortions':       'No. of Abortions',
    '  I   beta-HCG(mIU/mL)':'β-HCG (I)',
    'I   beta-HCG(mIU/mL)':  'β-HCG (I)',
    'II    beta-HCG(mIU/mL)': 'β-HCG (II)',
    'FSH(mIU/mL)':            'FSH Level',
    'LH(mIU/mL)':             'LH Level',
    'FSH/LH':                 'FSH / LH Ratio',
    'Hip(inch)':              'Hip Size',
    'Waist(inch)':            'Waist Size',
    'Waist:Hip Ratio':        'Waist-Hip Ratio',
    'TSH (mIU/L)':            'TSH Level',
    'AMH(ng/mL)':             'AMH Level',
    'PRL(ng/mL)':             'Prolactin',
    'Vit D3 (ng/mL)':         'Vitamin D3',
    'PRG(ng/mL)':             'Progesterone',
    'RBS(mg/dl)':             'Blood Sugar',
    'Weight gain(Y/N)':       'Weight Gain',
    'hair growth(Y/N)':       'Excess Hair Growth',
    'Skin darkening (Y/N)':   'Skin Darkening',
    'Hair loss(Y/N)':         'Hair Loss',
    'Pimples(Y/N)':           'Pimples / Acne',
    'Fast food (Y/N)':        'Fast Food Intake',
    'Reg.Exercise(Y/N)':      'Regular Exercise',
    'BP _Systolic (mmHg)':    'BP Systolic',
    'BP _Diastolic (mmHg)':   'BP Diastolic',
    'Follicle No. (L)':       'Follicle Count (L)',
    'Follicle No. (R)':       'Follicle Count (R)',
    'Avg. F size (L) (mm)':   'Avg Follicle Size (L)',
    'Avg. F size (R) (mm)':   'Avg Follicle Size (R)',
    'Endometrium (mm)':       'Endometrium Thickness',
}

def _tree_interpreter(model, scaled_input: np.ndarray) -> np.ndarray:
    """
    Tree Interpreter: exact per-prediction feature contributions for RandomForest.

    For each tree, walks the decision path from root to leaf.
    At each internal node, the feature used for the split gets credited
    with the change in class-1 probability between parent and child.
    Returns an array of shape (n_features,) with signed contributions
    that sum to (prediction - base_rate).
    """
    sample = scaled_input.reshape(1, -1)
    n_features = sample.shape[1]
    contributions = np.zeros(n_features)

    for tree in model.estimators_:
        tree_model = tree.tree_
        node_indicator = tree.decision_path(sample)
        node_ids = node_indicator.indices

        # Walk the path: each internal node contributes a probability shift
        for depth in range(len(node_ids) - 1):
            parent_id = node_ids[depth]
            child_id  = node_ids[depth + 1]
            feature_idx = tree_model.feature[parent_id]

            # Class-1 proportion at parent vs child
            parent_samples = tree_model.value[parent_id].flatten()
            child_samples  = tree_model.value[child_id].flatten()

            parent_prob = parent_samples[1] / parent_samples.sum() if parent_samples.sum() > 0 else 0
            child_prob  = child_samples[1] / child_samples.sum() if child_samples.sum() > 0 else 0

            contributions[feature_idx] += (child_prob - parent_prob)

    # Average across all trees
    contributions /= len(model.estimators_)
    return contributions


def _compute_key_factors(feature_vec: np.ndarray, scaled_vec: np.ndarray, risk_prob: float) -> list:
    """
    Compute per-prediction key factor contributions using Tree Interpreter.

    Each contribution is the exact probability shift caused by that feature's
    value as the prediction traverses the decision trees.  Positive contribution
    means the feature pushed the risk UP; negative means it pushed it DOWN.
    """
    if not hasattr(ModelStore.ML_MODEL, 'estimators_'):
        return []

    columns = ModelStore.X_COLUMNS
    contributions = _tree_interpreter(ModelStore.ML_MODEL, scaled_vec)

    factors = []
    for i, col in enumerate(columns):
        contrib = float(contributions[i])

        # Skip negligible contributions
        if abs(contrib) < 0.001:
            continue

        direction = 'increases_risk' if contrib > 0 else 'decreases_risk'
        label = FEATURE_LABELS.get(col, col.replace('(Y/N)', '').replace('(', '').replace(')', '').strip())

        factors.append({
            'feature':      col,
            'label':        label,
            'importance':   round(abs(contrib), 4),
            'raw_contrib':  round(contrib, 4),
            'value':        round(float(feature_vec[i]), 4),
            'direction':    direction,
        })

    # Sort by absolute contribution descending, take top 10
    factors.sort(key=lambda x: -x['importance'])
    top_factors = factors[:10]

    # Normalise importance to sum to 1.0 for clean percentage display
    total_imp = sum(f['importance'] for f in top_factors) or 1.0
    for f in top_factors:
        f['importance'] = round(f['importance'] / total_imp, 4)

    return top_factors


def ml_predict(user_input: Dict[str, Any]) -> Dict[str, Any]:
    if ModelStore.ML_MODEL is None:
        raise RuntimeError("ML model not loaded, unable to predict")

    feature_vec = build_feature_vector(user_input)
    scaled      = ModelStore.SCALER.transform(feature_vec.reshape(1, -1))
    proba       = ModelStore.ML_MODEL.predict_proba(scaled)[0]
    risk_prob   = float(proba[1])

    risk_pct = round(risk_prob * 100, 2)

    if risk_pct < 30:
        level = 'Low'
    elif risk_pct < 70:
        level = 'Moderate'
    else:
        level = 'High'

    # ── Per-prediction key factor analysis (Tree Interpreter) ──
    contributions = _compute_key_factors(feature_vec, scaled, risk_prob)

    bmi = None
    w = float(user_input.get('weight', 0) or 0)
    h = float(user_input.get('height', 0) or 0)
    if w > 0 and h > 0:
        bmi = round(w / ((h / 100) ** 2), 2)

    return {
        'risk_percentage': risk_pct,
        'risk_level': level,
        'confidence': round(float(max(proba)) * 100, 2),
        'bmi': bmi,
        'feature_contributions': contributions,
    }

def get_gemini_recommendations(user_input: Dict, risk_pct: float, risk_level: str) -> Dict[str, Any]:
    if not settings.GEMINI_API_KEY:
        return _static_recommendations(risk_level)
    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        age    = user_input.get('age', 'unknown')
        bmi    = user_input.get('bmi', 'unknown')
        cycle  = 'Regular' if user_input.get('cycle_regular', 1) == 1 else 'Irregular'
        weight = user_input.get('weight', 'unknown')

        prompt = f"""
You are a compassionate women's health advisor specializing in PCOS.
Patient Profile: Age: {age}, BMI: {bmi}, Menstrual Cycle: {cycle}, Weight: {weight} kg, PCOS Risk: {risk_pct}% ({risk_level} Risk)

Provide a structured response with EXACTLY these sections in JSON format:
{{
  "health_insights": ["3 brief insights"],
  "diet_plan": {{
    "include": ["5 specific foods"],
    "avoid": ["4 specific foods"],
    "meal_timing": "2-sentence advice"
  }},
  "exercise_plan": {{
    "weekly_schedule": [
      {{"day": "Monday", "activity": "30-min brisk walk", "duration": "30 min"}},
      {{"day": "Wednesday", "activity": "Yoga", "duration": "45 min"}},
      {{"day": "Friday", "activity": "Strength training", "duration": "40 min"}},
      {{"day": "Sunday", "activity": "Cycling", "duration": "45 min"}}
    ],
    "tip": "One sentence tip"
  }},
  "lifestyle_tips": ["5 practical daily habits"],
  "doctor_advice": "1 empathetic sentence"
}}
"""
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        recs = json.loads(text)
        recs['source'] = 'gemini'
        return recs
    except Exception as e:
        logger.error(f"Gemini LLM error: {e}")
        return _static_recommendations(risk_level)

def _static_recommendations(risk_level: str) -> Dict[str, Any]:
    base = {
        'health_insights': [
            'Your hormonal balance is a key factor in PCOS risk.',
            'Maintaining a healthy weight can significantly reduce symptoms.',
            'Regular physical activity helps regulate insulin and hormones.'
        ],
        'diet_plan': {
            'include': ['Leafy greens', 'Whole grains', 'Lean proteins', 'Berries', 'Healthy fats'],
            'avoid': ['Refined sugars', 'White bread', 'Processed foods', 'Excess dairy'],
            'meal_timing': 'Eat 3 balanced meals with 1-2 healthy snacks.'
        },
        'exercise_plan': {
            'weekly_schedule': [
                {'day': 'Monday', 'activity': 'Brisk walking', 'duration': '30 min'},
                {'day': 'Wednesday', 'activity': 'Yoga', 'duration': '45 min'},
                {'day': 'Friday', 'activity': 'Light strength training', 'duration': '40 min'},
                {'day': 'Sunday', 'activity': 'Cycling', 'duration': '45 min'},
            ],
            'tip': 'Exercise improves insulin sensitivity and helps regulate periods.'
        },
        'lifestyle_tips': [
            'Sleep 7–8 hours per night',
            'Stay hydrated',
            'Practice stress management',
            'Track your menstrual cycle',
            'Limit alcohol and avoid smoking'
        ],
        'doctor_advice': 'We encourage you to share these results with your gynecologist.',
        'source': 'static'
    }
    if risk_level == 'High':
        base['health_insights'].insert(0, '⚠️ Elevated risk. Please consult a healthcare provider soon.')
    return base

def get_cycle_diary_insights(user_history: list, new_entry: dict) -> dict:
    if not settings.GEMINI_API_KEY:
        return {
            "entry_confirmation": "Your entry has been recorded.",
            "cycle_summary": "Cycle data stored.",
            "insights": "Please add a Gemini API key for AI tracking.",
            "next_period_prediction": "Keep tracking to predict.",
            "tips": "Stay hydrated and rest well."
        }
    try:
        from google import genai
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
You are an AI assistant designed to help users track, maintain, and understand their menstrual cycle diary in a simple, supportive, and privacy-respecting way.

USER INPUT (New Entry):
- Date: {new_entry.get('date')}
- Period status: {new_entry.get('period_status')}
- Flow level: {new_entry.get('flow_level', 'None')}
- Symptoms: {', '.join(new_entry.get('symptoms', [])) if new_entry.get('symptoms') else 'None'}
- Mood: {new_entry.get('mood', 'None')}
- Notes: {new_entry.get('notes', 'None')}

PAST CYCLE HISTORY:
{json.dumps(user_history)}

FUNCTIONAL BEHAVIOR:
- Identify cycle start/end length if possible. Detect irregularities (Cycle < 21 days OR > 35 days).
- Estimate next period based on last 3 cycles if available. Otherwise, ask user to continue logging.
- If irregular cycles detected, suggest monitoring and consulting a doctor directly (without alarming tone).
- If symptoms severe, recommend medical advice gently.

OUTPUT FORMAT (Must be exactly this JSON structure, <120 words total):
{{
  "entry_confirmation": "✅ Your entry for [date] has been recorded",
  "cycle_summary": "1 sentence cycle summary",
  "insights": "1 sentence pattern insight based on history",
  "next_period_prediction": "1 sentence prediction",
  "tips": "1 short supportive suggestion"
}}

UX GUIDELINES:
- Use simple, friendly language. Empathetic and supportive.
- Do not assume missing data, don't generate false medical claims.
"""
        response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
        text = response.text.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()

        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini LLM Diary error: {e}")
        return {
            "entry_confirmation": f"✅ Your entry has been recorded.",
            "cycle_summary": "Data saved successfully.",
            "insights": "Keep logging to build your cycle patterns.",
            "next_period_prediction": "More data needed for an accurate prediction.",
            "tips": "Listen to your body and rest when needed."
        }

