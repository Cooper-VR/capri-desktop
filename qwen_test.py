import os

import torch
import soundfile as sf
from qwen_tts import Qwen3TTSModel

use_gpu = torch.cuda.is_available()
device = os.getenv("QWEN_DEVICE", "cuda:0" if use_gpu else "cpu")
dtype_name = os.getenv("QWEN_DTYPE", "bfloat16" if device.startswith("cuda") else "float32")
try:
    dtype = getattr(torch, dtype_name)
except AttributeError as error:
    raise ValueError("QWEN_DTYPE must be float32, float16, or bfloat16") from error
attention = os.getenv("QWEN_ATTENTION", "eager")

print(f"Loading Qwen on {device} with {dtype_name}...")
model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    device_map=device,
    dtype=dtype,
    attn_implementation=attention,
)

ref_audio = os.getenv(
    "QWEN_REFERENCE_AUDIO",
    "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-Repo/clone.wav",
)
ref_text = (
    "Okay. Yeah. I resent you. I love you. I respect you. "
    "But you know what? You blew it! And thanks to you."
)

print("Preparing the cloned voice...")
voice_prompt = model.create_voice_clone_prompt(
    ref_audio=ref_audio,
    ref_text=ref_text,
)

text = input("Text to speak (blank to quit): ").strip()
while text:
    wavs, sample_rate = model.generate_voice_clone(
        text=text,
        language="English",
        voice_clone_prompt=voice_prompt,
    )

    sf.write("qwen-test-output.wav", wavs[0], sample_rate)
    print("Created qwen-test-output.wav")
    text = input("Text to speak (blank to quit): ").strip()