# OmniVoice — RunPod Serverless Worker

TTS đa ngôn ngữ (600+) + clone giọng zero-shot (`k2-fsa/OmniVoice`) đóng gói thành
RunPod Serverless worker. Model được **bake sẵn trong image** → cold-start nhanh, scale-to-zero.

## Input / Output
- Input `job["input"]`: `{ "text": "...", "language": "vi", "ref_audio_b64": "...", "ref_text": "...", "voice_id": "...", "speed": 1.0 }`
- Output: `{ "wav_b64": "<base64 WAV 24kHz>", "sr": 24000 }`

## Deploy (cách trực tiếp — khuyên dùng)
1. RunPod Console → **Serverless** → **New Endpoint** → nguồn **GitHub**.
2. Lần đầu: **Connect GitHub** (OAuth) và cấp quyền đọc repo này.
3. Chọn repo `omnivoice-runpod`, branch `main`, Dockerfile `Dockerfile`.
4. GPU: RTX 3090 / 4090 (24GB đủ). Workers min 0 (scale-to-zero), max 1–3, FlashBoot ON.
5. Deploy → RunPod tự **build image** (~10–20 phút, có bake model 2GB) → tạo endpoint.
6. Lấy **Endpoint ID** → điền vào app: `RUNPOD_ENDPOINT_ID=...` trong `H:\omnivoice\.env`.

## Deploy (cách RunPod Hub)
Repo có `.runpod/hub.json` — có thể publish lên RunPod Hub rồi bấm Deploy.

Gọi thử: `POST https://api.runpod.ai/v2/<ENDPOINT_ID>/runsync` với header `Authorization: Bearer <RUNPOD_API_KEY>`.
