from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import numpy as np
import librosa
import scipy.io.wavfile as wav

MODEL_NAME = "vasista22/whisper-telugu-medium"

processor = None
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"


# ── Load Model ───────────────────────────────────────────────────────────────
def load_asr_model():
    global processor, model

    if model is None:
        print("Loading Telugu Whisper model...")

        processor = WhisperProcessor.from_pretrained(MODEL_NAME)
        model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)

        model.to(device)
        model.eval()

    return processor, model


# ── Transcription ────────────────────────────────────────────────────────────
def transcribe_audio(audio_path: str) -> str:
    try:
        proc, mdl = load_asr_model()

        # Read audio
        samplerate, audio = wav.read(audio_path)

        # Convert stereo → mono
        if len(audio.shape) > 1:
            audio = np.mean(audio, axis=1)

        # Normalize audio
        audio = audio.astype(np.float32) / 32768.0

        # Resample if needed
        if samplerate != 16000:
            audio = librosa.resample(audio, orig_sr=samplerate, target_sr=16000)

        # Process input
        inputs = proc(audio, sampling_rate=16000, return_tensors="pt")
        input_features = inputs.input_features.to(device)

        # 🔥 IMPORTANT: Force Telugu decoding
        forced_decoder_ids = proc.get_decoder_prompt_ids(
            language="te",
            task="transcribe"
        )

        # Generate text
        with torch.no_grad():
            predicted_ids = mdl.generate(
                input_features,
                forced_decoder_ids=forced_decoder_ids
            )

        # Decode output
        telugu_text = proc.batch_decode(
            predicted_ids,
            skip_special_tokens=True
        )[0]

        print("Telugu Transcript:", telugu_text)
        return telugu_text.strip()

    except Exception as e:
        print("ASR Error:", e)
        return ""


# ── Unload Model (optional) ──────────────────────────────────────────────────
def unload_model():
    global processor, model

    processor = None
    model = None

    if torch.cuda.is_available():
        torch.cuda.empty_cache()