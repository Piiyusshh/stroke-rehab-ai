# Simple rule-based predictor as fallback since sklearn installation failed
import os
from datetime import datetime

def predict_recovery_progress(age, nihss, adherence, weeks_post_stroke):
    """Predict recovery progress percentage using simple rules."""
    # Base progress: lower NIHSS and higher adherence -> better progress
    base_progress = 100 - (nihss * 2.5)  # NIHSS 0 = 100%, NIHSS 40 = 0%

    # Adjust for age: younger better
    age_adjust = max(0, (70 - age) * 0.5)

    # Adjust for adherence: more sessions better
    adherence_adjust = adherence * 3  # 3% per session/week

    # Adjust for time: progress increases over time but plateaus
    time_adjust = min(weeks_post_stroke * 2, 20)  # Up to 20% over time

    progress = base_progress + age_adjust + adherence_adjust + time_adjust
    return max(0, min(100, progress))  # Clip to 0-100
