# -*- coding: utf-8 -*-
"""RunPod Serverless QUEUE handler cho OmniVoice (model bake sẵn trong image).

Input  (job["input"]): {text, language?, ref_audio_b64?, ref_text?, voice_id?, speed?}
Output: {wav_b64, sr}   (wav 24kHz, base64)
"""
import os, io, base64, tempfile, threading
import numpy as np
import soundfile as sf
import runpod

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

SR = 24000
_model = None
_lock = threading.Lock()
_prompts = {}


def load():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                import torch
                from omnivoice import OmniVoice
                dev = "cuda:0" if torch.cuda.is_available() else "cpu"
                dt = torch.float16 if dev.startswith("cuda") else torch.float32
                print(f"[handler] loading OmniVoice on {dev} {dt}", flush=True)
                _model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=dev, dtype=dt)
                print("[handler] ready", flush=True)
    return _model


def _flatten(audio):
    if isinstance(audio, (list, tuple)):
        parts = [np.asarray(a, dtype=np.float32).reshape(-1) for a in audio if a is not None and len(a)]
        gap = np.zeros(int(0.12 * SR), dtype=np.float32)
        out = []
        for i, p in enumerate(parts):
            if i:
                out.append(gap)
            out.append(p)
        return np.concatenate(out) if out else np.zeros(1, dtype=np.float32)
    return np.asarray(audio, dtype=np.float32).reshape(-1)


def handler(job):
    inp = job.get("input", {}) or {}
    text = (inp.get("text") or "").strip()
    if not text:
        return {"error": "empty text"}
    ref_path = None
    try:
        m = load()
        kwargs = {"text": text}
        if inp.get("language"):
            kwargs["language"] = inp["language"]
        if inp.get("speed") is not None:
            kwargs["speed"] = float(inp["speed"])
        vid = inp.get("voice_id")
        with _lock:
            if vid and vid in _prompts:
                kwargs["voice_clone_prompt"] = _prompts[vid]
            elif inp.get("ref_audio_b64"):
                raw = base64.b64decode(inp["ref_audio_b64"])
                fd, ref_path = tempfile.mkstemp(suffix=".wav")
                os.write(fd, raw); os.close(fd)
                prompt = m.create_voice_clone_prompt(ref_path, ref_text=(inp.get("ref_text") or "").strip() or None)
                if vid:
                    _prompts[vid] = prompt
                kwargs["voice_clone_prompt"] = prompt
            audio = m.generate(**kwargs)
        wav = _flatten(audio)
        buf = io.BytesIO()
        sf.write(buf, wav, SR, format="WAV")
        return {"wav_b64": base64.b64encode(buf.getvalue()).decode("ascii"), "sr": SR}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if ref_path and os.path.exists(ref_path):
            try:
                os.remove(ref_path)
            except Exception:
                pass


runpod.serverless.start({"handler": handler})
