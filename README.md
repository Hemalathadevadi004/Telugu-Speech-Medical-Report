# 🏥 Telugu Speech to English Medical Report

> AI pipeline that converts a patient's spoken Telugu 
> complaint into a structured English medical report 
> automatically — no manual transcription needed.

## 🎯 Problem We Solved
82 million people speak Telugu. Doctors must mentally 
translate patient speech while writing notes — 
important details get lost.

Our system: Patient speaks Telugu → AI generates 
full medical report in 4.6 seconds.

## ⚙️ How It Works

Patient Speaks Telugu
        ↓
Whisper ASR → Telugu Text
        ↓
NLLB-200 → English Text
        ↓
BERT NER → Extracts 8 Fields
        ↓
Structured DOCX Report (Streamlit)

## 📋 8 Fields Extracted
- Patient Name
- Age
- Gender  
- Chief Complaint
- Duration
- Other Symptoms
- Past History
- Additional Info

## 🛠️ Tech Stack
- Python
- Whisper ASR (OpenAI)
- NLLB-200 (Meta AI)
- BERT NER (Hugging Face)
- Streamlit
- python-docx
- PyTorch

## 📊 Results
| Metric | Score | Target |
|--------|-------|--------|
| WER (Whisper) | 13.8% | < 15% ✅ |
| BLEU (NLLB) | 37.4 | > 30 ✅ |
| F1 (BERT NER) | 0.88 | > 0.80 ✅ |
| Processing Time | 4.6s | < 10s ✅ |

## 🔄 Project Status
- ✅ Phase 1 — Patient side (Completed)
- 🔄 Phase 2 — Doctor side (In Progress)
  - Under guidance of Dr. Motahar Reza
  - GITAM University, Hyderabad

## 👩‍💻 Developer
**Hemalatha Devadi**  
M.Sc. Data Science — GITAM University  
📧 Hemadevadi08@gmail.com  
🔗 linkedin.com/in/hemalathadevadi-5964a927b
