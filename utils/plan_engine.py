from datetime import datetime
from utils.ml_predictor import predict_recovery_progress

# Options for the HTML form (also useful for validation)
DEFAULT_FORM_OPTIONS = {
    "stroke_type": ["Ischemic", "Hemorrhagic", "TIA"],
    "affected_side": ["Left", "Right", "Both"],
    "goals": ["Walk independently", "Improve hand function", "Reduce spasticity", "Improve speech", "Enhance memory"],
    "comorbidities": ["Hypertension", "Diabetes", "Atrial fibrillation", "Depression", "Obesity", "Dyslipidemia"],
    "equipment": ["None", "Cane", "Walker", "Ankle-Foot Orthosis (AFO)"],
    "speech_issues": ["None", "Dysarthria", "Aphasia"],
    "cognitive_issues": ["None", "Attention", "Memory", "Executive function"]
}

def _to_int(value, name, minimum=None, maximum=None):
    try:
        iv = int(value)
    except Exception:
        raise ValueError(f"{name} must be an integer")
    if minimum is not None and iv < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    if maximum is not None and iv > maximum:
        raise ValueError(f"{name} must be <= {maximum}")
    return iv

def validate_input(data: dict):
    errors = []
    required_fields = ["age", "sex", "stroke_type", "nihss", "affected_side", "weeks_post_stroke"]
    for f in required_fields:
        if f not in data or str(data[f]).strip() == "":
            errors.append(f"Missing field: {f}")
    if "age" in data:
        try:
            _to_int(data["age"], "Age", 10, 110)
        except ValueError as e:
            errors.append(str(e))
    if "nihss" in data:
        try:
            _to_int(data["nihss"], "NIHSS", 0, 42)
        except ValueError as e:
            errors.append(str(e))
    if "weeks_post_stroke" in data:
        try:
            _to_int(data["weeks_post_stroke"], "Weeks post stroke", 0, 520)
        except ValueError as e:
            errors.append(str(e))
    if "stroke_type" in data and data["stroke_type"] not in DEFAULT_FORM_OPTIONS["stroke_type"]:
        errors.append("Invalid stroke_type")
    if "affected_side" in data and data["affected_side"] not in DEFAULT_FORM_OPTIONS["affected_side"]:
        errors.append("Invalid affected_side")
    if "speech_issues" in data and data["speech_issues"] not in DEFAULT_FORM_OPTIONS["speech_issues"]:
        errors.append("Invalid speech_issues")
    if "cognitive_issues" in data and data["cognitive_issues"] not in DEFAULT_FORM_OPTIONS["cognitive_issues"]:
        errors.append("Invalid cognitive_issues")
    return (len(errors) == 0, errors)

def _intensity_from_nihss(nihss: int):
    if nihss <= 4:
        return "mild"
    if nihss <= 15:
        return "moderate"
    return "severe"

def _minutes_per_session(intensity: str):
    return {"mild": 45, "moderate": 30, "severe": 20}[intensity]

def _sessions_per_week(intensity: str):
    return {"mild": 6, "moderate": 5, "severe": 4}[intensity]

def _strength_sets_reps(intensity: str):
    base = {"mild": (3, 12), "moderate": (2, 10), "severe": (2, 8)}[intensity]
    return {"sets": base[0], "reps": base[1]}

def _safety_notes(data):
    notes = []
    comorbid = set(data.get("comorbidities", []) or [])
    if "Hypertension" in comorbid:
        notes.append("Monitor BP pre/post session; avoid Valsalva.")
    if "Diabetes" in comorbid:
        notes.append("Check glucose pre-session; keep fast-acting carbs available.")
    if "Atrial fibrillation" in comorbid:
        notes.append("Watch for palpitations/dizziness; ensure rate control is stable.")
    if "Depression" in comorbid:
        notes.append("Include motivational interviewing; set short achievable goals.")
    if "Obesity" in comorbid:
        notes.append("Prefer low-impact aerobic work (recumbent cycle, pool therapy).")
    if "Dyslipidemia" in comorbid:
        notes.append("Emphasize aerobic conditioning and diet counseling.")
    if data.get("stroke_type") == "Hemorrhagic":
        notes.append("Start low intensity; avoid high BP spikes; gradual progression.")
    return notes

def _motor_exercises(intensity, affected_side, equipment):
    minutes = _minutes_per_session(intensity)
    freq = _sessions_per_week(intensity)
    strength = _strength_sets_reps(intensity)
    equip_note = "" if equipment == "None" else f" Use {equipment} as needed for gait safety."
    return [
        {
            "name": "Gait training",
            "details": f"{minutes} minutes, {freq}x/week on level surface; add obstacles and dual-task as tolerated." + equip_note
        },
        {
            "name": "Balance & proprioception",
            "details": f"{minutes//2} minutes, {freq}x/week; tandem stance, single-leg support on {affected_side.lower()} side support as tolerated."
        },
        {
            "name": "Task-specific practice (reach & grasp)",
            "details": f"{strength['sets']} sets × {strength['reps']} reps; constraint-induced practice if safe."
        },
        {
            "name": "Spasticity management",
            "details": "Daily prolonged stretching (≥ 30–60s/rep), weight-bearing and slow AROM; consider splinting if tone impedes function."
        },
        {
            "name": "Aerobic conditioning",
            "details": f"{minutes} minutes brisk walk/cycle/UBE at RPE 11–13, {freq}x/week."
        },
    ]

def _speech_exercises(speech_issue):
    if speech_issue == "Aphasia":
        return [
            {"name": "Naming & word retrieval", "details": "Picture naming, semantic feature analysis 15–20 min/day."},
            {"name": "Script training", "details": "Practice functional phrases (greetings, requests) 10–15 min/day."},
            {"name": "Group conversation", "details": "2–3x/week with caregiver involvement."},
        ]
    if speech_issue == "Dysarthria":
        return [
            {"name": "Respiratory-phonatory control", "details": "Breath support drills, sustained phonation 10 min/day."},
            {"name": "Articulation drills", "details": "Minimal pairs, over-articulation 15 min/day."},
            {"name": "Prosody practice", "details": "Vary stress and intonation using reading tasks 10 min/day."},
        ]
    return [{"name": "Communication maintenance", "details": "Daily reading aloud, conversational practice 10–15 min/day."}]

def _cognitive_exercises(issue):
    mapping = {
        "None": [{"name": "Cognitive wellness", "details": "Daily puzzles/reading 10–15 min."}],
        "Attention": [{"name": "Sustained/Selective attention", "details": "Target apps/tasks 15 min/day; reduce distractions."}],
        "Memory": [{"name": "Spaced retrieval", "details": "Practice names/appointments with spaced intervals 10–15 min/day."}],
        "Executive function": [{"name": "Planning & problem solving", "details": "Multi-step tasks (cooking checklists) 15–20 min/day."}],
    }
    return mapping.get(issue, mapping["None"])

def _goals_block(goals):
    if not goals:
        return []
    return [{"goal": g, "kpi": _kpi_for_goal(g)} for g in goals]

def _kpi_for_goal(goal):
    table = {
        "Walk independently": "10-m walk speed ≥ 0.8 m/s; TUG ≤ 13.5s",
        "Improve hand function": "Box & Blocks +20 blocks; Nine-Hole Peg −20% time",
        "Reduce spasticity": "Modified Ashworth −1 grade; AROM +10°",
        "Improve speech": "WAB naming +10%; intelligibility +20% (listener-rated)",
        "Enhance memory": "RBMT subtests +15%; independent use of memory aids"
    }
    return table.get(goal, "Patient-reported outcome improvement")

def generate_plan(data: dict, adherence=3):
    age = int(data.get("age"))
    sex = data.get("sex", "Other")
    stroke_type = data.get("stroke_type")
    nihss = int(data.get("nihss"))
    affected_side = data.get("affected_side")
    weeks = int(data.get("weeks_post_stroke"))
    equipment = data.get("equipment", "None")
    speech_issue = data.get("speech_issues", "None")
    cognitive_issue = data.get("cognitive_issues", "None")
    comorbidities = data.get("comorbidities", []) or []
    goals = data.get("goals", []) or []

    # Predict recovery progress using ML
    predicted_progress = predict_recovery_progress(age, nihss, adherence, weeks)

    intensity = _intensity_from_nihss(nihss)
    # Adjust intensity based on prediction: if low progress, increase intensity slightly
    if predicted_progress < 50 and intensity == "mild":
        intensity = "moderate"
    elif predicted_progress > 80 and intensity == "severe":
        intensity = "moderate"

    plan = {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "patient": {"age": age, "sex": sex},
            "clinical": {"stroke_type": stroke_type, "nihss": nihss, "affected_side": affected_side, "weeks_post_stroke": weeks},
            "intensity": intensity,
            "predicted_recovery_progress": round(predicted_progress, 1)
        },
        "schedule": {
            "sessions_per_week": _sessions_per_week(intensity),
            "minutes_per_session": _minutes_per_session(intensity),
        },
        "motor_exercises": _motor_exercises(intensity, affected_side, equipment),
        "speech_exercises": _speech_exercises(speech_issue),
        "cognitive_exercises": _cognitive_exercises(cognitive_issue),
        "goals": _goals_block(goals),
        "lifestyle": [
            "Sleep 7–9 hours; consistent schedule.",
            "Mediterranean-style diet; limit salt to <5g/day.",
            "Daily BP log; medication adherence reminders.",
            "Smoking cessation, limit alcohol; hydration 2–2.5L/day.",
            "Caregiver-assisted home safety: remove trip hazards; install grab bars."
        ],
        "safety": _safety_notes(data),
        "follow_up": [
            "Reassess every 2 weeks: NIHSS, 10-m walk, grip strength, WAB (if applicable).",
            "Progression rule: if pain >5/10 or fatigue >24h, step back 1 level.",
            f"Predicted recovery progress: {round(predicted_progress, 1)}%. Adjust plan based on actual progress."
        ]
    }

    if weeks >= 6 and intensity != "mild":
        plan["progression_hint"] = "Consider progressing intensity by one level based on tolerance and clinician approval."

    return plan
