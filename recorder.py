import sounddevice as sd
from scipy.io.wavfile import write

SAMPLERATE = 16000

def record_audio(duration: int = 10, filename: str = "patient_audio.wav") -> str:
    try:
        print(f"Recording for {duration} seconds...")

        audio = sd.rec(
            int(duration * SAMPLERATE),
            samplerate=SAMPLERATE,
            channels=1,
            dtype="int16"
        )

        sd.wait()  # Wait until recording is finished

        write(filename, SAMPLERATE, audio)

        print(f"Saved to {filename}")
        return filename

    except Exception as e:
        print("Error during recording:", e)
        return ""