import os
import requests
import streamlit as st
import time

st.set_page_config(page_title="PCOS Risk — Quick Form", layout="wide")

# ngrok friendly header
HEADERS = {"ngrok-skip-browser-warning": "true"}

default_api = os.environ.get('NGROK_URL', 'http://localhost:8000')
API_URL = st.sidebar.text_input('API base URL', default_api)

targets = st.sidebar.multiselect('Predict targets', options=['PCOS', 'PCOD'], default=['PCOS', 'PCOD'])

st.title('PCOS Risk — Quick Form')

# Inject custom CSS
st.markdown("""
<style>

/* ----------- APP BACKGROUND ----------- */
.stApp {
    background-color: #F4FAF9;
}

/* ----------- HEADINGS ----------- */
h1, h2, h3 {
    color: #0F2F36;
    font-weight: 700;
}

/* ----------- METRIC CARDS ----------- */
.metric-card {
    background: #FFFFFF;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #D7ECEB;
    box-shadow: 0 4px 10px rgba(0,0,0,0.04);
    text-align: center;
    transition: 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 18px rgba(0,0,0,0.06);
}

/* ----------- SECTION BOX ----------- */
.section-box {
    background: #FFFFFF;
    padding: 20px;
    border-radius: 16px;
    border: 1px solid #D7ECEB;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}

/* ----------- SIDEBAR ----------- */
section[data-testid="stSidebar"] {
    background-color: #E0F2F1;
}

/* ----------- BUTTONS ----------- */
.stButton > button {
    background-color: #1B9AAA;
    color: white;
    border-radius: 8px;
    border: none;
    padding: 8px 18px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: #157F87;
}

/* ----------- ALERT / ISSUE CARDS ----------- */
.issue-card {
    background: #FFF4F4;
    padding: 16px;
    border-radius: 14px;
    border-left: 6px solid #E63946;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* ----------- TABLE ----------- */
[data-testid="stData hookup Frame"] {
    border-radius: 12px;
    border: 1px solid #D7ECEB;
}

    /* Hide radio circles */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Radio item container */
    div[role="radiogroup"] label {
        padding: 6px 10px;
        margin: 4px 0;
        border-radius: 6px;
        font-size: 15px;
        cursor: pointer;
    }

    /* Hover */
    div[role="radiogroup"] label:hover {
        background-color: #f2f2f2;
    }

    /* Active item */
    div[role="radiogroup"] input:checked + div {
        background-color:  #f1f3f4;
        font-weight: 600;
        border-radius: 6px;
        padding: 6px 10px;
    }

</style>
""", unsafe_allow_html=True)

with st.form('input_form'):
    age = st.number_input('Age (yrs)', min_value=0, max_value=120, value=25)
    weight = st.number_input('Weight (Kg)', min_value=0.0, value=60.0)
    height = st.number_input('Height (cm)', min_value=0.0, value=160.0)
    pulse = st.number_input('Pulse rate (bpm)', min_value=0, value=72)
    rr = st.number_input('RR (breaths/min)', min_value=0, value=16)
    hb = st.number_input('Hb (g/dl)', min_value=0.0, value=12.0)
    cycle_length = st.number_input('Cycle length (days)', min_value=0, value=28)
    waist = st.number_input('Waist (inch)', min_value=0.0, value=30.0)
    hip = st.number_input('Hip (inch)', min_value=0.0, value=36.0)
    tsh = st.number_input('TSH (mIU/L)', min_value=0.0, value=2.5)
    amh = st.number_input('AMH (ng/mL)', min_value=0.0, value=2.0)
    prl = st.number_input('PRL (ng/mL)', min_value=0.0, value=10.0)
    vitd = st.number_input('Vit D3 (ng/mL)', min_value=0.0, value=20.0)
    rbs = st.number_input('RBS (mg/dl)', min_value=0.0, value=90.0)

    submitted = st.form_submit_button('Get Risk')

if submitted:
    payload = {
        'data': {
            'Age': age,
            'Weight': weight,
            'Height': height,
            'Pulse rate(bpm)': pulse,
            'RR (breaths/min)': rr,
            'Hb(g/dl)': hb,
            'Cycle_length': cycle_length,
            'Waist(inch)': waist,
            'Hip(inch)': hip,
            'TSH (mIU/L)': tsh,
            'AMH(ng/mL)': amh,
            'PRL(ng/mL)': prl,
            'Vit D3 (ng/mL)': vitd,
            'RBS(mg/dl)': rbs,
        }
    }
    payload['targets'] = targets
    try:
        resp = requests.post(f"{API_URL}/predict", json=payload, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        # If backend returns per-target mapping
        if isinstance(data, dict) and any(t in data for t in targets):
            for t in targets:
                entry = data.get(t)
                if not entry:
                    st.warning(f"No result for {t}")
                    continue
                st.subheader(f"{t} — {entry.get('risk_level', '')} ({entry.get('risk_percentage', '')}%)")
                if entry.get('top_explanations'):
                    st.markdown('**Top feature contributions**')
                    for f in entry['top_explanations']:
                        val = f.get('shap_value', f.get('contribution'))
                        if val is None:
                            st.write(f"{f.get('feature', 'feature')}: (no value)")
                        else:
                            try:
                                st.write(f"{f.get('feature', 'feature')}: {float(val):.4f}")
                            except Exception:
                                st.write(f"{f.get('feature', 'feature')}: {val}")
        # Single-target style response
        elif isinstance(data, dict) and 'risk_percentage' in data:
            st.success(f"Risk: {data['risk_percentage']}% ({data['risk_level']})")
            if 'top_explanations' in data:
                st.subheader('Top feature contributions')
                for f in data['top_explanations']:
                    val = f.get('shap_value', f.get('contribution'))
                    if val is None:
                        st.write(f"{f.get('feature', 'feature')}: (no value)")
                    else:
                        try:
                            st.write(f"{f.get('feature', 'feature')}: {float(val):.4f}")
                        except Exception:
                            st.write(f"{f.get('feature', 'feature')}: {val}")
        else:
            st.write(data)
    except Exception as e:
        st.error(f'Prediction failed: {e}')
