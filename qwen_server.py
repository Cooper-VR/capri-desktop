import os
from io import BytesIO

import soundfile as sf
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from qwen_tts import Qwen3TTSModel


class SpeechRequest(BaseModel):
    text: str


app = FastAPI()
device = os.getenv("QWEN_DEVICE", "cuda:0" if torch.cuda.is_available() else "cpu")
dtype_name = os.getenv("QWEN_DTYPE", "float16" if device.startswith("cuda") else "float32")
attention = os.getenv("QWEN_ATTENTION", "sdpa")

try:
    dtype = getattr(torch, dtype_name)
except AttributeError as error:
    raise RuntimeError("QWEN_DTYPE must be float32, float16, or bfloat16.") from error

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    device_map=device,
    dtype=dtype,
    attn_implementation=attention,
)

reference_audio = os.getenv(
    "QWEN_REFERENCE_AUDIO",
    "CapriAudio.wav",
)
reference_text = (
    "I'm Capri. Better off letting spiky hair hold onto it. He's a bit of a dummy but he's our best option to keep the chip safe for now. You broke so I made some repairs. Cost me an arm and a leg you know, my finest work."
)
voice_clone_prompt = model.create_voice_clone_prompt(
    ref_audio=reference_audio,
    ref_text=reference_text,
)


@app.get("/health")
def health():
    return {"ready": True, "device": device}


@app.post("/synthesize")
def synthesize(request: SpeechRequest):
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required.")

    try:
        wavs, sample_rate = model.generate_voice_clone(
            text=text,
            language="English",
            voice_clone_prompt=voice_clone_prompt,
            non_streaming_mode=True,
        )
        output = BytesIO()
        sf.write(output, wavs[0], sample_rate, format="WAV")
        return Response(content=output.getvalue(), media_type="audio/wav")
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
