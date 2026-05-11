import re
from typing import Dict, List

SYMPTOM_KEYWORDS = [
    "fever", "pain", "cough", "headache", "vomiting", "nausea",
    "dizziness", "fatigue", "breathlessness", "chest pain",
    "stomach ache", "cold", "weakness", "swelling", "rash",
    "burning", "itching", "bleeding", "loose motion", "diarrhea",
    "constipation", "loss of appetite", "weight loss", "body ache",
    "sore throat", "runny nose", "back pain", "joint pain",
    "palpitations", "anxiety", "depression", "insomnia", "numbness"
]

PAST_HISTORY_KEYWORDS = [
    "diabetes", "hypertension", "asthma", "heart disease", "thyroid",
    "kidney disease", "liver disease", "epilepsy", "cancer", "surgery",
    "accident", "fracture", "tuberculosis", "tb", "hiv", "hepatitis"
]

FAMILY_HISTORY_KEYWORDS = [
    "father", "mother", "brother", "sister",
    "grandfather", "grandmother", "parents", "family"
]

HABIT_KEYWORDS = [
    "smoking", "alcohol", "tobacco", "drugs", "exercise", "diet"
]

REQUIRED_FIELDS = [
    "patient_name", "age", "gender", "chief_complaint",
    "duration", "symptoms", "past_history", "allergies"
]


def extract_patient_slots(english_text: str) -> Dict:
    text_lower = english_text.lower()

    slots: Dict = {
        # Basic
        "patient_name":     "",
        "age":              "",
        "gender":           "",
        "phone":            "",
        "address":          "",
        # Chief Complaint
        "chief_complaint":  "",
        "duration":         "",
        # Symptoms
        "symptoms":         [],
        "other_symptoms":   [],
        # History
        "past_history":     [],
        "surgical_history": "",
        "family_history":   "",
        "menstrual_history":"",
        # Habits & Vitals
        "habits":           [],
        "temperature":      "",
        "blood_pressure":   "",
        "pulse":            "",
        "weight":           "",
        "height":           "",
        "allergies":        "",
        # Full transcript
        "notes":            english_text,
        # Tracking
        "_auto_filled":     [],
        "_missing":         []
    }

    def mark(field: str):
        if field not in slots["_auto_filled"]:
            slots["_auto_filled"].append(field)

    # ── Name ─────────────────────────────────────────────────────────────────
    m = re.search(
        r"(?:my name is|i am|i'm|name[:\s]+|patient[:\s]+)"
        r"([A-Za-z]+(?:\s[A-Za-z]+){0,2})",
        english_text, re.IGNORECASE
    )
    if m:
        slots["patient_name"] = m.group(1).strip().title()
        mark("patient_name")

    # ── Age ───────────────────────────────────────────────────────────────────
    m = re.search(r"(\d{1,3})\s*(?:years?|yr)(?:\s*old)?", text_lower)
    if m:
        slots["age"] = m.group(1)
        mark("age")

    # ── Gender ────────────────────────────────────────────────────────────────
    if re.search(r"\b(he|him|male|man|boy)\b", text_lower):
        slots["gender"] = "Male";   mark("gender")
    elif re.search(r"\b(she|her|female|woman|girl)\b", text_lower):
        slots["gender"] = "Female"; mark("gender")

    # ── Phone ─────────────────────────────────────────────────────────────────
    m = re.search(r"\b(\d{10})\b", english_text)
    if m:
        slots["phone"] = m.group(1)
        mark("phone")

    # ── Chief Complaint ───────────────────────────────────────────────────────
    m = re.search(
        r"(?:suffering from|having|complaining of|"
        r"problem (?:is|with)|came (?:with|for))\s+([^.,]+)",
        text_lower
    )
    if m:
        slots["chief_complaint"] = m.group(1).strip().title()
        mark("chief_complaint")

    # ── Duration ──────────────────────────────────────────────────────────────
    m = re.search(
        r"(?:for|since|last|past)\s+"
        r"(\d+\s*(?:day|days|week|weeks|month|months|hour|hours|year|years))",
        text_lower
    )
    if m:
        slots["duration"] = m.group(1)
        mark("duration")

    # ── Symptoms ──────────────────────────────────────────────────────────────
    found: List[str] = [
        kw.title() for kw in SYMPTOM_KEYWORDS if kw in text_lower
    ]
    if found:
        slots["symptoms"]       = found[:3]
        slots["other_symptoms"] = found[3:]
        mark("symptoms")

    # ── Past History ──────────────────────────────────────────────────────────
    hist = [kw.title() for kw in PAST_HISTORY_KEYWORDS if kw in text_lower]
    if hist:
        slots["past_history"] = hist
        mark("past_history")

    # ── Surgical History ──────────────────────────────────────────────────────
    if re.search(r"\b(operation|surgery|operated|surgical)\b", text_lower):
        m = re.search(
            r"(?:operation|surgery|operated|surgical)"
            r"\s*(?:for|on|of)?\s*([^.,]{0,40})",
            text_lower
        )
        if m:
            slots["surgical_history"] = m.group(0).strip().title()
            mark("surgical_history")

    # ── Family History ────────────────────────────────────────────────────────
    for kw in FAMILY_HISTORY_KEYWORDS:
        if kw in text_lower:
            m = re.search(
                rf"{kw}\s+(?:has|had|is|was|suffering|died)\s+([^.,]{{0,40}})",
                text_lower
            )
            if m:
                slots["family_history"] = m.group(0).strip().title()
                mark("family_history")
                break

    # ── Habits ────────────────────────────────────────────────────────────────
    habits = [kw.title() for kw in HABIT_KEYWORDS if kw in text_lower]
    if habits:
        slots["habits"] = habits
        mark("habits")

    # ── Vitals ────────────────────────────────────────────────────────────────
    m = re.search(r"(\d{2,3}/\d{2,3})", english_text)
    if m:
        slots["blood_pressure"] = m.group(1);  mark("blood_pressure")

    m = re.search(r"(\d{2,3}(?:\.\d)?)\s*(?:°f|°c|f|degrees?)", text_lower)
    if m:
        slots["temperature"] = m.group(1);     mark("temperature")

    m = re.search(r"(\d{2,3})\s*(?:bpm|pulse|heart rate)", text_lower)
    if m:
        slots["pulse"] = m.group(1);           mark("pulse")

    m = re.search(r"(\d{2,3})\s*(?:kg|kgs|kilograms?)", text_lower)
    if m:
        slots["weight"] = m.group(1);          mark("weight")

    # ── Allergies ─────────────────────────────────────────────────────────────
    m = re.search(
        r"(?:allergic to|allergy to|allergy[:\s]+)([^.,]+)", text_lower
    )
    if m:
        slots["allergies"] = m.group(1).strip().title()
        mark("allergies")

    # ── Missing Fields ────────────────────────────────────────────────────────
    for field in REQUIRED_FIELDS:
        v = slots[field]
        if not v or v == []:
            slots["_missing"].append(field)

    return slots