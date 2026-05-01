"""
HerHealthAI — Rule-Based Expert Recommendation Engine
======================================================
Tiered, deterministic, LLM-free recommendation system.

Tier 1: Risk Level  — selects the base plan (Low / Moderate / High)
Tier 2: Overlays    — injects symptom/feature-specific additions
Tier 3: Format      — builds the final structured JSON output

All rules are loaded from app/data/rules.json — editable without
touching this code.
"""

import json
import copy
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# ── Load rule dictionary once at startup ────────────────────────────────────
_RULES_PATH = Path(__file__).parent.parent / "data" / "rules.json"

def _load_rules() -> Dict:
    try:
        with open(_RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"rules.json not found at {_RULES_PATH}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"rules.json is malformed: {e}")
        return {}

_RULES: Dict = _load_rules()


# ── Tier 1: Risk-Level Base Plan ─────────────────────────────────────────────

def _get_base_plan(risk_level: str) -> Dict:
    """Return a deep copy of the base plan for the given risk level."""
    key_map = {"Low": "LOW_RISK", "Moderate": "MODERATE_RISK", "High": "HIGH_RISK"}
    key = key_map.get(risk_level, "MODERATE_RISK")
    base = _RULES.get(key, _RULES.get("MODERATE_RISK", {}))
    return copy.deepcopy(base)


# ── Tier 2: Feature-Based Overlay Injections ─────────────────────────────────

def _apply_overlays(plan: Dict, user_input: Dict, risk_level: str, lifestyle_profile: Dict = None) -> Dict:
    """
    Inspect user features and inject relevant symptom-specific advice
    on top of the base plan. Each overlay is independent and additive.
    Applies Tier 2 (medical features) and Tier 3 (lifestyle features) overlays.
    """
    overlays = _RULES.get("SYMPTOM_OVERLAYS", {})
    lifestyle_overlays = _RULES.get("LIFESTYLE_OVERLAYS", {})

    downgrade_intensity = False

    def _inject(overlay_dict: Dict, overlay_key: str):
        nonlocal downgrade_intensity
        ov = overlay_dict.get(overlay_key, {})
        if not ov:
            return

        # Diet additions
        for item in ov.get("diet_add", []):
            if item not in plan["diet"]["include"]:
                plan["diet"]["include"].append(item)

        # Diet avoidance
        for item in ov.get("diet_avoid", []):
            if item not in plan["diet"]["avoid"]:
                plan["diet"]["avoid"].append(item)

        # Exercise additions (as extra schedule entries)
        for item in ov.get("exercise_add", []):
            entry = {"day": "Additional", "activity": item, "duration": "—"}
            if entry not in plan["exercise"]["weekly_schedule"]:
                plan["exercise"]["weekly_schedule"].append(entry)

        # Lifestyle additions
        for item in ov.get("lifestyle_add", []):
            if item not in plan["lifestyle"]["tips"]:
                plan["lifestyle"]["tips"].append(item)
                
        if ov.get("exercise_downgrade_intensity"):
            downgrade_intensity = True

    # --- Tier 2: Medical Feature Overlays ---
    # ── BMI check ──────────────────────────────────────────────────────────
    bmi = float(user_input.get("bmi") or 0)
    if bmi == 0:
        w = float(user_input.get("weight") or 0)
        h = float(user_input.get("height") or 0)
        if w > 0 and h > 0:
            bmi = round(w / ((h / 100) ** 2), 2)
    if bmi > 25:
        _inject(overlays, "high_bmi")

    # ── Acne / Pimples ─────────────────────────────────────────────────────
    if user_input.get("pimples") == 1:
        _inject(overlays, "pimples_acne")

    # ── Hair Issues ────────────────────────────────────────────────────────
    if user_input.get("hair_loss") == 1 or user_input.get("hair_growth") == 1:
        _inject(overlays, "hair_loss_growth")

    # ── Elevated Blood Sugar ────────────────────────────────────────────────
    rbs = float(user_input.get("rbs") or 0)
    if rbs > 140:
        _inject(overlays, "high_rbs")

    # ── Irregular Menstrual Cycle ───────────────────────────────────────────
    if user_input.get("cycle_regular") == 0:
        _inject(overlays, "irregular_cycle")

    # ── Low Vitamin D3 ─────────────────────────────────────────────────────
    vitd = float(user_input.get("vitd") or 0)
    if 0 < vitd < 20:
        _inject(overlays, "low_vitd")

    # ── Fertility Focus (married > 5 years + moderate/high risk) ───────────
    marriage_years = float(user_input.get("marriage_years") or 0)
    if marriage_years > 5 and risk_level in ("Moderate", "High"):
        _inject(overlays, "fertility_focus")

    # ── Sedentary / No Exercise ─────────────────────────────────────────────
    if user_input.get("exercise") == 0:
        _inject(overlays, "sedentary_no_exercise")

    # ── High Fast Food Intake ───────────────────────────────────────────────
    if user_input.get("fast_food") == 1:
        _inject(overlays, "high_fast_food")

    # --- Tier 3: Lifestyle Profile Overlays ---
    if lifestyle_profile:
        # Check new inputs mapping to the updated rules.json LIFESTYLE_OVERLAYS
        stress = lifestyle_profile.get("stress_level", "").lower()
        if stress == "high":
            _inject(lifestyle_overlays, "stress_high")
            
        activity = lifestyle_profile.get("activity_level", "").lower()
        if activity == "sedentary":
            _inject(lifestyle_overlays, "activity_sedentary")

        freq = lifestyle_profile.get("exercise_frequency", "").lower()
        if freq == "none":
            _inject(lifestyle_overlays, "exercise_none")
        elif freq == "daily":
            _inject(lifestyle_overlays, "exercise_daily")

        water = lifestyle_profile.get("water_intake", "").lower()
        if water == "low":
            _inject(lifestyle_overlays, "water_low")
            
        job = lifestyle_profile.get("job_type", "").lower()
        if "corporate" in job or "desk" in job:
            _inject(lifestyle_overlays, "job_corporate")
        elif "sports" in job or "athlete" in job:
            _inject(lifestyle_overlays, "job_sports")
        elif "student" in job:
            _inject(lifestyle_overlays, "job_student")
        elif "homemaker" in job:
            _inject(lifestyle_overlays, "job_homemaker")

    # Handle intensity downgrades if requested by lifestyle constraints
    if downgrade_intensity:
        # Filter out high intensity exercises if lifestyle demands it
        original_schedule = plan["exercise"]["weekly_schedule"]
        plan["exercise"]["weekly_schedule"] = [
            ex for ex in original_schedule 
            if not any(word in ex.get("activity", "").lower() for word in ["squats", "push-ups", "strength", "hiit"])
        ]
        if "High intensity workouts have been removed from your plan due to high stress or sedentary lifestyle." not in plan["exercise"]["tip"]:
            plan["exercise"]["tip"] += " High intensity workouts have been removed from your plan due to high stress or sedentary baseline to prevent burnout/cortisol spikes."

    return plan

    # ── BMI check ──────────────────────────────────────────────────────────
    bmi = float(user_input.get("bmi") or 0)
    if bmi == 0:
        w = float(user_input.get("weight") or 0)
        h = float(user_input.get("height") or 0)
        if w > 0 and h > 0:
            bmi = round(w / ((h / 100) ** 2), 2)
    if bmi > 25:
        _inject("high_bmi")

    # ── Acne / Pimples ─────────────────────────────────────────────────────
    if user_input.get("pimples") == 1:
        _inject("pimples_acne")

    # ── Hair Issues ────────────────────────────────────────────────────────
    if user_input.get("hair_loss") == 1 or user_input.get("hair_growth") == 1:
        _inject("hair_loss_growth")

    # ── Elevated Blood Sugar ────────────────────────────────────────────────
    rbs = float(user_input.get("rbs") or 0)
    if rbs > 140:
        _inject("high_rbs")

    # ── Irregular Menstrual Cycle ───────────────────────────────────────────
    if user_input.get("cycle_regular") == 0:
        _inject("irregular_cycle")

    # ── Low Vitamin D3 ─────────────────────────────────────────────────────
    vitd = float(user_input.get("vitd") or 0)
    if 0 < vitd < 20:
        _inject("low_vitd")

    # ── Fertility Focus (married > 5 years + moderate/high risk) ───────────
    marriage_years = float(user_input.get("marriage_years") or 0)
    if marriage_years > 5 and risk_level in ("Moderate", "High"):
        _inject("fertility_focus")

    # ── Sedentary / No Exercise ─────────────────────────────────────────────
    if user_input.get("exercise") == 0:
        _inject("sedentary_no_exercise")

    # ── High Fast Food Intake ───────────────────────────────────────────────
    if user_input.get("fast_food") == 1:
        _inject("high_fast_food")

    return plan


# ── Tier 3: Health Insights Builder ──────────────────────────────────────────

def _build_health_insights(user_input: Dict, risk_pct: float, risk_level: str) -> list:
    """
    Return customized health insights based on the user's specific risk factors and symptoms.
    """
    insights = []
    
    # 1. Base Insight based on Risk Level
    if risk_level == "High":
        insights.append(f"Your assessment indicates a high PCOS risk ({risk_pct:.1f}%). Early intervention and consulting a healthcare provider are strongly recommended.")
    elif risk_level == "Moderate":
        insights.append(f"Your assessment indicates a moderate PCOS risk ({risk_pct:.1f}%). Proactive lifestyle adjustments can help manage symptoms.")
    else:
        insights.append(f"Your assessment indicates a low PCOS risk ({risk_pct:.1f}%). Maintaining your current healthy habits is key.")

    # 2. BMI Insight
    bmi = float(user_input.get("bmi") or 0)
    if bmi == 0:
        w = float(user_input.get("weight") or 0)
        h = float(user_input.get("height") or 0)
        if w > 0 and h > 0:
            bmi = round(w / ((h / 100) ** 2), 2)
            
    if bmi >= 25:
        insights.append(f"Your BMI is {bmi:.1f}. A 5-10% reduction in body weight can significantly improve menstrual regularity and hormonal balance.")

    # 3. Cycle Regularity
    if user_input.get("cycle_regular") == 0:
        insights.append("Irregular menstrual cycles are a core indicator of hormonal imbalance. Tracking your cycle will be highly beneficial.")
        
    # 4. Hyperandrogenism signs (acne, hair growth, hair loss)
    androgen_symptoms = []
    if user_input.get("pimples") == 1: androgen_symptoms.append("acne")
    if user_input.get("hair_growth") == 1: androgen_symptoms.append("excess body hair")
    if user_input.get("hair_loss") == 1: androgen_symptoms.append("hair thinning")
    
    if androgen_symptoms:
        symptom_str = " and ".join(androgen_symptoms)
        insights.append(f"Symptoms like {symptom_str} suggest elevated androgen levels, which are common in PCOS and can be managed through diet and medication.")

    # 5. Lifestyle (Fast food and exercise)
    if user_input.get("fast_food") == 1 and user_input.get("exercise") == 0:
        insights.append("Combining a lack of exercise with frequent fast food significantly increases insulin resistance. This is a critical area for improvement.")
    elif user_input.get("fast_food") == 1:
        insights.append("Frequent consumption of processed/fast foods can spike blood sugar and worsen insulin resistance.")
    elif user_input.get("exercise") == 0:
        insights.append("Regular physical activity helps regulate insulin and hormones. Starting with just 20 minutes a day can make a big difference.")
        
    # Ensure we always have at least 3 insights
    general_insights = [
        "Your hormonal balance is a key factor in overall reproductive health.",
        "Managing stress levels helps keep cortisol in check, which indirectly supports hormonal balance.",
        "A diet rich in whole foods and fiber is foundational for managing PCOS symptoms."
    ]
    
    for general in general_insights:
        if len(insights) >= 3:
            break
        if general not in insights:
            insights.append(general)

    return insights


# ── Public Interface ──────────────────────────────────────────────────────────

def get_rule_based_recommendations(
    user_input: Dict[str, Any],
    risk_pct: float,
    risk_level: str,
    lifestyle_profile: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Main entry point for the recommendation engine.

    Parameters
    ----------
    user_input        : dict of feature values from PredictRequest
    risk_pct          : float — risk percentage from the ML model (0–100)
    risk_level        : str  — 'Low', 'Moderate', or 'High'
    lifestyle_profile : dict — optional lifestyle profile data

    Returns
    -------
    dict with keys: health_insights, diet_plan, exercise_plan,
                    lifestyle_tips, doctor_advice, source, sleep_suggestions
    """
    if not _RULES:
        logger.warning("Rule dictionary is empty — returning minimal fallback.")
        return {
            "health_insights": ["Rule engine could not load. Please check rules.json."],
            "diet_plan": {"include": [], "avoid": [], "meal_timing": ""},
            "exercise_plan": {"weekly_schedule": [], "tip": ""},
            "lifestyle_tips": [],
            "sleep_suggestions": [],
            "doctor_advice": "Please consult a healthcare provider.",
            "source": "fallback"
        }

    # Tier 1: Base plan from risk level
    plan = _get_base_plan(risk_level)

    # Tier 2 & 3: Symptom and Lifestyle overlays
    plan = _apply_overlays(plan, user_input, risk_level, lifestyle_profile)

    # Health insights are primarily based on clinical features
    insights = _build_health_insights(user_input, risk_pct, risk_level)

    sleep_suggestions = []
    # Compile personalized notes and filters from lifestyle if available
    personalized_notes = {}
    if lifestyle_profile:
        if lifestyle_profile.get("stress_level", "").lower() == "high":
            personalized_notes["stress_management"] = "Since you reported High stress, managing cortisol is your #1 priority right now. We have downgraded exercise intensity."
        
        # Build sleep suggestions
        sleep_dur = lifestyle_profile.get("sleep_duration", "")
        wake = lifestyle_profile.get("wake_up_time", "")
        
        if wake:
            sleep_suggestions.append(f"Based on your wake-up time of {wake}, ensure you stop consuming caffeine at least 10 hours prior to sleep.")
        if sleep_dur in ["<5 hours", "5-6 hours"]:
            sleep_suggestions.append(f"Your sleep duration ({sleep_dur}) is critically low. Sleep deprivation directly worsens insulin resistance and LH levels.")
            sleep_suggestions.append("Maintain a strict cool-down routine 1 hour before bed (no screens, dim lights).")
        elif sleep_dur in ["6-7 hours"]:
            sleep_suggestions.append("You are close to the optimal sleep duration. Try to add 30-45 minutes to your schedule.")
        else:
            sleep_suggestions.append("Great job maintaining a healthy sleep duration. This is highly beneficial for hormonal balance.")
            
        # Food preference diet filtering
        food_pref = lifestyle_profile.get("food_preference", "").lower()
        if food_pref == "vegan":
            plan["diet"]["avoid"].extend(["All dairy products (Milk, Curd, Ghee)", "Meat and eggs"])
            plan["diet"]["include"].append("Plant-based protein sources like Tofu, Tempeh, and lentils")
        elif food_pref == "veg":
            plan["diet"]["avoid"].extend(["Meat, poultry, and seafood"])

    result = {
        "health_insights": insights,
        "diet_plan": {
            "strategy":     plan["diet"].get("strategy", ""),
            "include":      plan["diet"].get("include", []),
            "avoid":        plan["diet"].get("avoid", []),
            "meal_timing":  plan["diet"].get("meal_timing", "")
        },
        "exercise_plan": {
            "weekly_schedule": plan["exercise"].get("weekly_schedule", []),
            "tip":             plan["exercise"].get("tip", "")
        },
        "lifestyle_tips":  plan["lifestyle"].get("tips", []),
        "sleep_suggestions": sleep_suggestions,
        "doctor_advice":   plan["lifestyle"].get("doctor_advice", ""),
        "source":          "rule_based_engine"
    }

    if personalized_notes:
        result["personalized_notes"] = personalized_notes

    return result
