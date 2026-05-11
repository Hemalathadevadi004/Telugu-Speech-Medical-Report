from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib import colors

# ── Color Palette ─────────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#1a5276")
MID_BLUE   = colors.HexColor("#2980b9")
LIGHT_BLUE = colors.HexColor("#eaf4fb")
GRID_COLOR = colors.HexColor("#aed6f1")
ORANGE     = colors.HexColor("#d35400")
WHITE      = colors.white


# ── Helpers ───────────────────────────────────────────────────────────────────
def _val(d: Dict, key: str, default: str = "N/A") -> str:
    v = d.get(key)
    if isinstance(v, list):
        return ", ".join(str(i) for i in v) if v else default
    return str(v).strip() if v else default


def _make_table(
    data: List[List[str]],
    col_widths: List = None,
    has_header: bool = True
) -> Table:
    col_widths = col_widths or [5*cm, 12*cm]
    t = Table(data, colWidths=col_widths)
    style = [
        ("GRID",         (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("FONTNAME",     (0, 0), (0,  -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",      (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS",(0, 0),(-1, -1), [LIGHT_BLUE, WHITE]),
        ("WORDWRAP",     (0, 0), (-1, -1), True),
    ]
    if has_header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR",  (0, 0), (-1, 0), WHITE),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, 0), 11),
        ]
    t.setStyle(TableStyle(style))
    return t


# ── Plain Text Report ─────────────────────────────────────────────────────────
def generate_report_text(
    patient_slots: Dict,
    doctor_slots:  Optional[Dict] = None
) -> str:

    now = datetime.now().strftime("%d-%m-%Y  %H:%M")
    p   = patient_slots

    def pv(key: str) -> str:
        return _val(p, key)

    lines = f"""
========================================
       MEDICAL CONSULTATION REPORT
========================================
  Date & Time   : {now}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. PATIENT INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Name          : {pv('patient_name')}
  Age           : {pv('age')} years
  Gender        : {pv('gender')}
  Phone         : {pv('phone')}
  Address       : {pv('address')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  2. CHIEF COMPLAINT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Chief Complaint : {pv('chief_complaint')}
  Duration        : {pv('duration')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  3. SYMPTOMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Main Symptoms   : {pv('symptoms')}
  Other Symptoms  : {pv('other_symptoms')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  4. VITALS  (Patient Reported)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Temperature     : {pv('temperature')}
  Blood Pressure  : {pv('blood_pressure')}
  Pulse           : {pv('pulse')} bpm
  Weight          : {pv('weight')} kg
  Height          : {pv('height')} cm

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  5. HISTORY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Past Medical    : {pv('past_history')}
  Surgical        : {pv('surgical_history')}
  Family          : {pv('family_history')}
  Menstrual       : {pv('menstrual_history')}
  Habits          : {pv('habits')}
  Allergies       : {pv('allergies')}

  Patient Notes   : {pv('notes')}
"""

    if doctor_slots:
        d = doctor_slots

        def dv(key: str) -> str:
            return _val(d, key)

        meds = d.get("medications", [])
        meds_str = ("\n" + " " * 18).join(meds) if meds else "N/A"

        lines += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  6. DOCTOR'S ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Examination     : {dv('examination')}
  Diagnosis       : {dv('diagnosis')}
  Severity        : {dv('severity')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  7. TREATMENT PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Medications     : {meds_str}
  Tests Ordered   : {dv('tests')}
  Follow-up       : {dv('followup')}
  Referral        : {dv('referral')}
  Doctor Notes    : {dv('doctor_notes')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Doctor Name     : {dv('doctor_name')}
  Reg. Number     : {dv('doctor_reg')}
  Signature       : _______________
  Date            : {datetime.now().strftime('%d-%m-%Y')}
========================================
"""

    return lines.strip()


# ── PDF Report ────────────────────────────────────────────────────────────────
def generate_pdf_report(
    patient_slots: Dict,
    doctor_slots:  Optional[Dict] = None,
    output_path:   str = "medical_report.pdf"
) -> str:

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm,   bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()
    story  = []

    def sec(number: str, title: str, color=DARK_BLUE):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            f"{number}. {title}",
            ParagraphStyle(
                "Sec", parent=styles["Heading2"],
                fontSize=12, textColor=color,
                spaceBefore=6, spaceAfter=4
            )
        ))

    # ── Title Block ───────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Medical Consultation Report",
        ParagraphStyle("Title", parent=styles["Title"],
                       fontSize=22, textColor=DARK_BLUE, spaceAfter=2)
    ))
    story.append(Paragraph(
        f"Date: {datetime.now().strftime('%d %B %Y')}  |  "
        f"Time: {datetime.now().strftime('%H:%M')}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2.5, color=DARK_BLUE))

    # ── 1. Patient Information ────────────────────────────────────────────────
    sec("1", "Patient Information")
    story.append(_make_table([
        ["Field",   "Details"],
        ["Name",    _val(patient_slots, "patient_name")],
        ["Age",     f"{_val(patient_slots, 'age')} years"],
        ["Gender",  _val(patient_slots, "gender")],
        ["Phone",   _val(patient_slots, "phone")],
        ["Address", _val(patient_slots, "address")],
    ]))

    # ── 2. Chief Complaint ────────────────────────────────────────────────────
    sec("2", "Chief Complaint")
    story.append(_make_table([
        ["Field",            "Details"],
        ["Chief Complaint",  _val(patient_slots, "chief_complaint")],
        ["Duration",         _val(patient_slots, "duration")],
    ]))

    # ── 3. Symptoms ───────────────────────────────────────────────────────────
    sec("3", "Symptoms")
    story.append(_make_table([
        ["Field",           "Details"],
        ["Main Symptoms",   _val(patient_slots, "symptoms")],
        ["Other Symptoms",  _val(patient_slots, "other_symptoms")],
    ]))

    # ── 4. Vitals ─────────────────────────────────────────────────────────────
    sec("4", "Vitals (Patient Reported)")
    story.append(_make_table([
        ["Field",            "Details"],
        ["Temperature",      _val(patient_slots, "temperature")],
        ["Blood Pressure",   _val(patient_slots, "blood_pressure")],
        ["Pulse",            f"{_val(patient_slots, 'pulse')} bpm"],
        ["Weight",           f"{_val(patient_slots, 'weight')} kg"],
        ["Height",           f"{_val(patient_slots, 'height')} cm"],
    ]))

    # ── 5. History ────────────────────────────────────────────────────────────
    sec("5", "Medical History")
    hist_data = [
        ["Field",                "Details"],
        ["Past Medical History", _val(patient_slots, "past_history")],
        ["Surgical History",     _val(patient_slots, "surgical_history")],
        ["Family History",       _val(patient_slots, "family_history")],
        ["Habits",               _val(patient_slots, "habits")],
        ["Allergies",            _val(patient_slots, "allergies")],
    ]
    if patient_slots.get("gender") == "Female":
        hist_data.append(
            ["Menstrual History", _val(patient_slots, "menstrual_history")]
        )
    story.append(_make_table(hist_data))

    # ── 6. Patient Notes ──────────────────────────────────────────────────────
    sec("6", "Patient's Own Words")
    story.append(Paragraph(
        patient_slots.get("notes", "N/A"),
        styles["Normal"]
    ))

    # ── Doctor Section Divider ────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ORANGE))

    if doctor_slots:
        # ── 7. Doctor's Assessment ────────────────────────────────────────────
        sec("7", "Doctor's Assessment", color=ORANGE)
        story.append(_make_table([
            ["Field",                "Details"],
            ["Examination Findings", _val(doctor_slots, "examination")],
            ["Diagnosis",            _val(doctor_slots, "diagnosis")],
            ["Severity",             _val(doctor_slots, "severity")],
        ]))

        # ── 8. Treatment Plan ─────────────────────────────────────────────────
        sec("8", "Treatment Plan", color=ORANGE)
        meds     = doctor_slots.get("medications", [])
        meds_str = "\n".join(meds) if meds else "N/A"
        story.append(_make_table([
            ["Field",          "Details"],
            ["Medications",    meds_str],
            ["Tests Ordered",  _val(doctor_slots, "tests")],
            ["Follow-up",      _val(doctor_slots, "followup")],
            ["Referral",       _val(doctor_slots, "referral")],
        ]))

        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            f"<b>Doctor's Notes:</b> {doctor_slots.get('doctor_notes', 'N/A')}",
            styles["Normal"]
        ))
    else:
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            "[ Doctor's Assessment — to be filled after consultation ]",
            styles["Normal"]
        ))

    # ── Signature Block ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRID_COLOR))
    story.append(Spacer(1, 0.3*cm))
    story.append(_make_table([
        ["Doctor Name",    doctor_slots.get("doctor_name", "")   if doctor_slots else ""],
        ["Reg. Number",    doctor_slots.get("doctor_reg",  "")   if doctor_slots else ""],
        ["Signature",      "_______________"],
        ["Date",           datetime.now().strftime("%d-%m-%Y")],
    ], has_header=False))

    doc.build(story)
    print(f"PDF saved: {output_path}")
    return output_path