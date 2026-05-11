import streamlit as st
from recorder      import record_audio
from asr           import transcribe_audio
from translator    import translate_to_english
from slot_extractor import extract_patient_slots
from report_generator import generate_report_text, generate_pdf_report

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediScript AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main { background-color: #f0f4f8; }

.card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    border-left: 4px solid #1a5276;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}

.section-header {
    background: linear-gradient(90deg, #1a5276, #2980b9);
    color: white;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    margin: 16px 0 10px 0;
}

.patient-bar {
    background: #1a5276;
    color: white;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 14px;
    margin-bottom: 12px;
}

.step-box {
    background: #eaf4fb;
    border: 1px solid #aed6f1;
    border-radius: 10px;
    padding: 12px;
    text-align: center;
    font-weight: 600;
    color: #1a5276;
    margin-bottom: 4px;
}
.step-done   { background:#d4edda; border-color:#28a745; color:#155724; }
.step-active { background:#fff3cd; border-color:#ffc107; color:#856404; }

.badge-green { background:#d4edda; color:#155724; padding:3px 10px;
               border-radius:20px; font-size:12px; font-weight:600; }
.badge-orange{ background:#fff3cd; color:#856404; padding:3px 10px;
               border-radius:20px; font-size:12px; font-weight:600; }
.badge-red   { background:#f8d7da; color:#721c24; padding:3px 10px;
               border-radius:20px; font-size:12px; font-weight:600; }

.report-box {
    background:#f8f9fa; border:1px solid #dee2e6;
    border-radius:8px; padding:16px;
    font-family:'Courier New',monospace;
    font-size:13px; white-space:pre-wrap;
    max-height:500px; overflow-y:auto;
}

#MainMenu {visibility:hidden;} footer {visibility:hidden;}

.stTabs [data-baseweb="tab-list"] {
    gap:8px; background:white;
    padding:8px; border-radius:10px; margin-bottom:8px;
}
.stTabs [data-baseweb="tab"] {
    height:44px; padding:0 20px;
    border-radius:8px; font-weight:600;
}
.stButton > button {
    border-radius:8px; font-weight:600; transition:all 0.2s;
}
.stButton > button:hover {
    transform:translateY(-1px);
    box-shadow:0 4px 12px rgba(0,0,0,0.15);
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _step(label, state):
    cls = "step-done" if state == "done" else \
          "step-active" if state == "active" else "step-box"
    icon = "✅" if state == "done" else \
           "🔄" if state == "active" else "⬜"
    st.markdown(
        f'<div class="step-box {cls}">{icon} {label}</div>',
        unsafe_allow_html=True
    )


def section(title: str):
    st.markdown(
        f'<div class="section-header">{title}</div>',
        unsafe_allow_html=True
    )


def patient_bar():
    ps  = st.session_state.get("patient_slots", {})
    n   = ps.get("patient_name") or "—"
    a   = ps.get("age")          or "—"
    g   = ps.get("gender")       or "—"
    cc  = ps.get("chief_complaint") or "—"
    sym = ", ".join(ps.get("symptoms", [])[:2]) or "—"
    st.markdown(
        f'<div class="patient-bar">'
        f'🧑 <b>{n}</b> &nbsp;|&nbsp; Age: <b>{a}</b> &nbsp;|&nbsp; '
        f'Gender: <b>{g}</b> &nbsp;|&nbsp; '
        f'Chief Complaint: <b>{cc}</b> &nbsp;|&nbsp; '
        f'Symptoms: <b>{sym}</b></div>',
        unsafe_allow_html=True
    )


def field_label(key, label, auto, missing):
    if key in auto:    return f"✅ {label}"
    if key in missing: return f"⚠️ {label} (fill this)"
    return label


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 MediScript AI")
    st.caption("Telugu Speech → Medical Report")
    st.markdown("---")

    st.markdown("### ⚙️ Settings")
    duration = st.slider("🎙️ Recording Duration (sec)", 5, 60, 15)
    make_pdf  = st.checkbox("📄 Generate PDF Report", value=True)

    st.markdown("---")
    st.markdown("### 📊 Session Status")

    has_audio   = "audio_file"    in st.session_state
    has_patient = "patient_slots" in st.session_state
    has_doctor  = "doctor_slots"  in st.session_state

    st.markdown(
        f'<span class="badge-{"green" if has_audio else "red"}">'
        f'🎙️ Audio: {"Ready" if has_audio else "Not recorded"}</span>',
        unsafe_allow_html=True
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if has_patient:
        ps      = st.session_state["patient_slots"]
        filled  = ps.get("_auto_filled", [])
        missing = ps.get("_missing",     [])
        st.markdown(
            f'<span class="badge-green">✅ Auto-filled: {len(filled)}</span>',
            unsafe_allow_html=True
        )
        if missing:
            st.markdown(
                f'<span class="badge-orange">⚠️ Missing: {len(missing)}</span>',
                unsafe_allow_html=True
            )
            for m in missing:
                st.caption(f"  • {m.replace('_',' ').title()}")
        else:
            st.markdown(
                '<span class="badge-green">✅ All fields filled!</span>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<span class="badge-red">📋 No patient data</span>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f'<span class="badge-{"green" if has_doctor else "orange"}">'
        f'🩺 Doctor: {"Saved" if has_doctor else "Not filled"}</span>',
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.markdown("### 🤖 Models")
    st.caption("ASR : vasista22/whisper-telugu-medium")
    st.caption("NMT : GoogleTranslator (deep-translator)")
    st.caption("NLP : Regex + Keyword matching")
    st.markdown("---")
    st.caption("v3.0 · MediScript AI")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1a5276,#2980b9);
            padding:20px 28px;border-radius:14px;margin-bottom:16px;">
  <h1 style="color:white;margin:0;font-size:28px;">🏥 MediScript AI</h1>
  <p  style="color:#aed6f1;margin:4px 0 0;font-size:15px;">
      Telugu Patient Speech → Automatic English Medical Report
  </p>
</div>
""", unsafe_allow_html=True)

# ── Progress Steps ────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1: _step("Record Audio",   "done"   if has_audio   else "pending")
with c2: _step("Extract Info",   "done"   if has_patient else
                                 "active" if has_audio   else "pending")
with c3: _step("Doctor Review",  "done"   if has_doctor  else
                                 "active" if has_patient else "pending")
with c4: _step("Final Report",   "done"   if (has_patient and has_doctor) else
                                 "active" if has_doctor  else "pending")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🎙️  Step 1 · Patient Recording",
    "🩺  Step 2 · Doctor Assessment",
    "📋  Step 3 · Final Report"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PATIENT RECORDING
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── Audio Input ───────────────────────────────────────────────────────────
    section("🎤  Record or Upload Patient Speech (Telugu)")
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔴 Live Microphone")
        st.caption(f"Duration: **{duration} sec** (change in sidebar)")
        if st.button("🔴  Start Recording", use_container_width=True, type="primary"):
            with st.spinner(f"🎤 Recording {duration} seconds — speak in Telugu..."):
                audio_file = record_audio(duration=duration)
                st.session_state["audio_file"] = audio_file
            st.success("✅ Recording saved!")
        if st.session_state.get("audio_file") == "patient_audio.wav":
            st.audio("patient_audio.wav")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📁 Upload Audio File")
        st.caption("Supports WAV and MP3")
        uploaded = st.file_uploader(
            "Drop file here", type=["wav", "mp3"],
            label_visibility="collapsed"
        )
        if uploaded:
            with open("uploaded_audio.wav", "wb") as f:
                f.write(uploaded.read())
            st.session_state["audio_file"] = "uploaded_audio.wav"
            st.success(f"✅ Uploaded: {uploaded.name}")
            st.audio("uploaded_audio.wav")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Process Button ────────────────────────────────────────────────────────
    section("⚙️  Process: Transcribe → Translate → Extract")

    col_btn, col_msg = st.columns([2, 3])
    with col_btn:
        proc_btn = st.button(
            "⚙️  Transcribe & Extract Patient Info",
            use_container_width=True, type="primary",
            disabled="audio_file" not in st.session_state
        )
    with col_msg:
        if "audio_file" not in st.session_state:
            st.warning("⬅️ Record or upload audio first")

    if proc_btn:
        try:
            prog = st.progress(0, text="Starting...")

            prog.progress(10, text="🎤 Step 1/3 — Transcribing Telugu audio...")
            telugu_text = transcribe_audio(st.session_state["audio_file"])
            st.session_state["telugu_text"] = telugu_text
            prog.progress(40, text="✅ Transcription done!")

            prog.progress(45, text="🌐 Step 2/3 — Translating to English...")
            english_text = translate_to_english(telugu_text)
            st.session_state["english_text"] = english_text
            prog.progress(75, text="✅ Translation done!")

            prog.progress(80, text="🔍 Step 3/3 — Extracting medical slots...")
            patient_slots = extract_patient_slots(english_text)
            st.session_state["patient_slots"] = patient_slots
            prog.progress(100, text="✅ Extraction complete!")

            filled  = patient_slots.get("_auto_filled", [])
            missing = patient_slots.get("_missing",     [])

            m1, m2, m3 = st.columns(3)
            m1.metric("🎤 Telugu Words",   len(telugu_text.split()))
            m2.metric("✅ Fields Extracted", len(filled))
            m3.metric("⚠️ Fields Missing",  len(missing))

            if missing:
                st.warning(
                    f"⚠️ Not found in speech — please fill below: "
                    f"**{', '.join(x.replace('_',' ').title() for x in missing)}**"
                )
            else:
                st.success("🎉 All required fields extracted!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.exception(e)

    # ── Transcript Preview ────────────────────────────────────────────────────
    if "telugu_text" in st.session_state:
        with st.expander("📝 View Transcripts", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Telugu Transcript**")
                st.text_area("", st.session_state["telugu_text"],
                             height=90, label_visibility="collapsed",
                             key="prev_tel")
            with c2:
                st.markdown("**English Translation**")
                st.text_area("", st.session_state.get("english_text",""),
                             height=90, label_visibility="collapsed",
                             key="prev_eng")

    # ══════════════════════════════════════════════════════════════════════════
    # PATIENT FORM
    # ══════════════════════════════════════════════════════════════════════════
    if "patient_slots" in st.session_state:
        ps      = st.session_state["patient_slots"]
        auto    = ps.get("_auto_filled", [])
        missing = ps.get("_missing",     [])

        pct = int(100 * len(auto) / max(len(auto) + len(missing), 1))
        badge_cls = "badge-green" if pct >= 80 else \
                    "badge-orange" if pct >= 50 else "badge-red"

        st.markdown("---")
        section("📋  Review & Complete Patient Information")

        col_info, col_pct = st.columns([4, 1])
        with col_info:
            st.caption("✅ = extracted from speech   |   ⚠️ = not found, please fill")
        with col_pct:
            st.markdown(
                f'<span class="{badge_cls}">Form: {pct}% complete</span>',
                unsafe_allow_html=True
            )

        # 1 — Basic Info
        st.markdown("#### 👤 Basic Information")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ps["patient_name"] = st.text_input(
                field_label("patient_name","Patient Name", auto, missing),
                value=ps.get("patient_name",""), placeholder="Full name"
            )
        with c2:
            ps["age"] = st.text_input(
                field_label("age","Age (years)", auto, missing),
                value=ps.get("age",""), placeholder="e.g. 35"
            )
        with c3:
            g_opts = ["","Male","Female","Other"]
            cur_g  = ps.get("gender","")
            ps["gender"] = st.selectbox(
                field_label("gender","Gender", auto, missing),
                g_opts,
                index=g_opts.index(cur_g) if cur_g in g_opts else 0
            )
        with c4:
            ps["phone"] = st.text_input(
                field_label("phone","Phone", auto, missing),
                value=ps.get("phone",""), placeholder="10-digit"
            )

        ps["address"] = st.text_input(
            "🏠 Address / Area",
            value=ps.get("address",""),
            placeholder="City, Area, Pincode"
        )

        # 2 — Chief Complaint
        st.markdown("#### 🤒 Chief Complaint")
        c1, c2 = st.columns(2)
        with c1:
            ps["chief_complaint"] = st.text_input(
                field_label("chief_complaint","Chief Complaint", auto, missing),
                value=ps.get("chief_complaint",""),
                placeholder="e.g. Fever with headache"
            )
        with c2:
            ps["duration"] = st.text_input(
                field_label("duration","Duration", auto, missing),
                value=ps.get("duration",""),
                placeholder="e.g. 3 days, 2 weeks"
            )

        # 3 — Symptoms
        st.markdown("#### 🔴 Symptoms")
        c1, c2 = st.columns(2)
        with c1:
            sym_in = st.text_area(
                field_label("symptoms","Main Symptoms (comma separated)", auto, missing),
                value=", ".join(ps.get("symptoms",[])),
                placeholder="e.g. Fever, Cough, Headache",
                height=80
            )
            ps["symptoms"] = [s.strip() for s in sym_in.split(",") if s.strip()]
        with c2:
            oth_in = st.text_area(
                "➕ Other / Associated Symptoms",
                value=", ".join(ps.get("other_symptoms",[])),
                placeholder="e.g. Weakness, Loss of appetite",
                height=80
            )
            ps["other_symptoms"] = [s.strip() for s in oth_in.split(",") if s.strip()]

        # 4 — History
        st.markdown("#### 📋 Medical History")
        c1, c2, c3 = st.columns(3)
        with c1:
            pst_in = st.text_area(
                field_label("past_history","Past Medical History", auto, missing),
                value=", ".join(ps.get("past_history",[])),
                placeholder="e.g. Diabetes, Hypertension",
                height=80
            )
            ps["past_history"] = [s.strip() for s in pst_in.split(",") if s.strip()]
        with c2:
            ps["surgical_history"] = st.text_area(
                "🔪 Surgical History",
                value=ps.get("surgical_history",""),
                placeholder="e.g. Appendectomy 2019",
                height=80
            )
        with c3:
            ps["family_history"] = st.text_area(
                "👨‍👩‍👧 Family History",
                value=ps.get("family_history",""),
                placeholder="e.g. Father — Diabetes",
                height=80
            )

        if ps.get("gender") == "Female":
            ps["menstrual_history"] = st.text_input(
                "🩸 Menstrual History",
                value=ps.get("menstrual_history",""),
                placeholder="e.g. Regular, LMP 10 days ago"
            )

        # 5 — Habits & Allergies
        st.markdown("#### 🚬 Habits & Allergies")
        c1, c2 = st.columns(2)
        with c1:
            hab_in = st.text_input(
                "Habits (Smoking / Alcohol / Tobacco etc.)",
                value=", ".join(ps.get("habits",[])),
                placeholder="e.g. Smoker 5 yrs, No alcohol"
            )
            ps["habits"] = [h.strip() for h in hab_in.split(",") if h.strip()]
        with c2:
            ps["allergies"] = st.text_input(
                field_label("allergies","Known Allergies", auto, missing),
                value=ps.get("allergies",""),
                placeholder="e.g. Penicillin, Sulfa, Dust"
            )

        # 6 — Vitals
        st.markdown("#### 💓 Vitals (Patient Reported)")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            ps["temperature"] = st.text_input(
                field_label("temperature","Temp °F", auto, missing),
                value=ps.get("temperature",""), placeholder="e.g. 101.4"
            )
        with c2:
            ps["blood_pressure"] = st.text_input(
                field_label("blood_pressure","BP mmHg", auto, missing),
                value=ps.get("blood_pressure",""), placeholder="e.g. 130/85"
            )
        with c3:
            ps["pulse"] = st.text_input(
                field_label("pulse","Pulse bpm", auto, missing),
                value=ps.get("pulse",""), placeholder="e.g. 88"
            )
        with c4:
            ps["weight"] = st.text_input(
                field_label("weight","Weight kg", auto, missing),
                value=ps.get("weight",""), placeholder="e.g. 68"
            )
        with c5:
            ps["height"] = st.text_input(
                "📏 Height cm",
                value=ps.get("height",""), placeholder="e.g. 168"
            )

        # 7 — Notes
        st.markdown("#### 📝 Additional Notes")
        ps["notes"] = st.text_area(
            "Patient's own words / anything else",
            value=ps.get("notes",""),
            height=80,
            placeholder="Any other info the patient mentioned..."
        )

        # ── Save ──────────────────────────────────────────────────────────────
        st.markdown("---")
        c1, c2 = st.columns([3, 1])
        with c1:
            if st.button("💾  Save Patient Info & Continue →",
                         use_container_width=True, type="primary"):
                still = [
                    lbl for k, lbl in {
                        "patient_name": "Patient Name",
                        "age":          "Age",
                        "chief_complaint": "Chief Complaint",
                        "symptoms":     "Symptoms"
                    }.items()
                    if not ps.get(k) or ps.get(k) == []
                ]
                if still:
                    st.warning(
                        f"⚠️ Still missing: **{', '.join(still)}** — "
                        "report may be incomplete, but you can continue."
                    )
                else:
                    st.success("✅ Saved! Go to 🩺 Doctor Assessment tab.")
                st.session_state["patient_slots"] = ps

        with c2:
            if st.button("🔄 Reset", use_container_width=True):
                for k in ["audio_file","telugu_text","english_text",
                          "patient_slots","doctor_slots"]:
                    st.session_state.pop(k, None)
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DOCTOR'S ASSESSMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    if "patient_slots" not in st.session_state:
        st.warning("⚠️ Complete Step 1 (Patient Recording) first.")
        st.stop()

    patient_bar()
    section("🩺  Doctor's Clinical Assessment")

    # Pre-fill if already saved
    ds = st.session_state.get("doctor_slots", {})

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🏥 Examination & Diagnosis")
        examination = st.text_area(
            "Clinical Examination Findings",
            value=ds.get("examination",""),
            placeholder="e.g. Throat congested\nLungs clear\nAbdomen soft",
            height=100
        )
        diagnosis_input = st.text_area(
            "⚕️ Diagnosis (comma separated)",
            value=", ".join(ds.get("diagnosis",[])),
            placeholder="e.g. Viral Fever, Acute Pharyngitis",
            height=80
        )
        sev_opts = ["","Mild","Moderate","Severe","Critical"]
        cur_sev  = ds.get("severity","")
        severity = st.selectbox(
            "📊 Severity",
            sev_opts,
            index=sev_opts.index(cur_sev) if cur_sev in sev_opts else 0
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 💊 Treatment Plan")
        medications_input = st.text_area(
            "Medications (one per line)",
            value="\n".join(ds.get("medications",[])),
            placeholder=(
                "Tab. Paracetamol 500mg — TDS × 5 days\n"
                "Tab. Cetirizine 10mg — OD × 5 days"
            ),
            height=100
        )
        tests_input = st.text_area(
            "🔬 Tests / Investigations",
            value=ds.get("tests",""),
            placeholder="e.g. CBC, Blood Sugar, Chest X-Ray",
            height=80
        )
        st.markdown('</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📅 Follow-up & Referral")
        followup = st.text_input(
            "Follow-up Instructions",
            value=ds.get("followup",""),
            placeholder="e.g. Review after 5 days"
        )
        referral = st.text_input(
            "↗️ Referral",
            value=ds.get("referral",""),
            placeholder="e.g. Referred to Cardiologist"
        )
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 👨‍⚕️ Doctor Details")
        doctor_name = st.text_input(
            "Doctor's Full Name",
            value=ds.get("doctor_name",""),
            placeholder="Dr. First Last"
        )
        doctor_reg = st.text_input(
            "Registration Number",
            value=ds.get("doctor_reg",""),
            placeholder="e.g. AP-MCI-12345"
        )
        doctor_notes = st.text_area(
            "📝 Doctor's Notes",
            value=ds.get("doctor_notes",""),
            placeholder="Additional clinical observations...",
            height=60
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("💾  Save Doctor's Assessment & Continue →",
                 use_container_width=True, type="primary"):
        st.session_state["doctor_slots"] = {
            "doctor_name"  : doctor_name,
            "doctor_reg"   : doctor_reg,
            "examination"  : examination,
            "diagnosis"    : [d.strip() for d in
                              diagnosis_input.replace("\n",",").split(",")
                              if d.strip()],
            "severity"     : severity,
            "medications"  : [m.strip() for m in
                              medications_input.split("\n") if m.strip()],
            "tests"        : tests_input,
            "followup"     : followup,
            "referral"     : referral,
            "doctor_notes" : doctor_notes
        }
        st.success("✅ Doctor's assessment saved! Go to 📋 Final Report tab.")
        st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — FINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
with tab3:

    if "patient_slots" not in st.session_state:
        st.warning("⚠️ No data yet. Complete Steps 1 and 2 first.")
        st.stop()

    patient_slots = st.session_state["patient_slots"]
    doctor_slots  = st.session_state.get("doctor_slots", None)

    patient_bar()

    # Metrics
    missing = patient_slots.get("_missing", [])
    m1, m2, m3 = st.columns(3)
    m1.metric("📋 Patient Fields", f"{len(patient_slots.get('_auto_filled',[]))} filled")
    m2.metric("⚠️ Missing Fields",  len(missing))
    m3.metric("🩺 Doctor Assessment", "✅ Done" if doctor_slots else "❌ Not filled")

    if missing:
        st.warning(
            f"⚠️ Incomplete — missing: "
            f"{', '.join(x.replace('_',' ').title() for x in missing)}"
        )

    st.markdown("---")

    # ── Report Preview ────────────────────────────────────────────────────────
    section("📄  Report Preview")
    report_text = generate_report_text(patient_slots, doctor_slots)
    st.markdown(
        f'<div class="report-box">{report_text}</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ── Downloads ─────────────────────────────────────────────────────────────
    section("⬇️  Download Report")
    safe_name = (
        patient_slots.get("patient_name","patient")
        .replace(" ","_").lower()
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "📄  Download TXT",
            data=report_text,
            file_name=f"report_{safe_name}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with c2:
        if make_pdf:
            if st.button("🖨️  Generate PDF",
                         use_container_width=True, type="primary"):
                with st.spinner("Generating PDF..."):
                    pdf_path = generate_pdf_report(patient_slots, doctor_slots)
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "⬇️  Download PDF",
                        data=f,
                        file_name=f"report_{safe_name}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
    with c3:
        if st.button("🔄  New Patient", use_container_width=True):
            for k in ["audio_file","telugu_text","english_text",
                      "patient_slots","doctor_slots"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ── Quick Edit ────────────────────────────────────────────────────────────
    with st.expander("✏️  Quick Edit Patient Details", expanded=False):
        ps = patient_slots
        c1, c2, c3 = st.columns(3)
        with c1:
            ps["patient_name"]    = st.text_input("Name",  ps.get("patient_name",""),  key="qe_n")
            ps["age"]             = st.text_input("Age",   ps.get("age",""),            key="qe_a")
        with c2:
            ps["chief_complaint"] = st.text_input("Chief Complaint",
                                                  ps.get("chief_complaint",""),         key="qe_cc")
            ps["duration"]        = st.text_input("Duration", ps.get("duration",""),   key="qe_d")
        with c3:
            ps["blood_pressure"]  = st.text_input("BP",    ps.get("blood_pressure",""),key="qe_bp")
            ps["temperature"]     = st.text_input("Temp",  ps.get("temperature",""),   key="qe_t")

        sym_qe = st.text_area("Symptoms", ", ".join(ps.get("symptoms",[])),
                               height=60, key="qe_sym")
        ps["symptoms"] = [s.strip() for s in sym_qe.split(",") if s.strip()]

        if st.button("💾  Update Report", type="primary"):
            st.session_state["patient_slots"] = ps
            st.rerun()