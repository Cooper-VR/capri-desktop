from pathlib import Path
import os
import subprocess
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from faster_whisper import WhisperModel
import numpy as np

app = FastAPI()

model_name = os.getenv("WHISPER_MODEL", "base")
device = os.getenv("WHISPER_DEVICE", "cpu")
compute_type = os.getenv(
    "WHISPER_COMPUTE_TYPE",
    "int8" if device == "cpu" else "float16",
)

model = WhisperModel(
    model_name,
    device=device,
    compute_type=compute_type,
)


def decode_audio(path: str) -> np.ndarray:
    try:
        converted = subprocess.run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-i",
                path,
                "-f",
                "f32le",
                "-ac",
                "1",
                "-ar",
                "16000",
                "pipe:1",
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as error:
        raise RuntimeError("ffmpeg is required and must be available on PATH.") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError("ffmpeg could not decode the audio: " + detail) from error

    audio = np.frombuffer(converted.stdout, dtype=np.float32)
    if audio.size == 0:
        raise RuntimeError("The uploaded audio contains no samples.")
    return audio


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temporary:
            temporary.write(await audio.read())
            temporary_path = temporary.name

        decoded = decode_audio(temporary_path)
        segments, info = model.transcribe(
            decoded,
            beam_size=5,
            vad_filter=True,
            language="en",
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

        return {
            "text": text,
            "language": info.language,
            "duration": info.duration,
        }

    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)