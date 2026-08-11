# OmniVoice — RunPod Serverless worker (bake sẵn deps + model để cold-start nhanh)
FROM runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404

ENV HF_HUB_ENABLE_HF_TRANSFER=1
WORKDIR /

# Cài dependencies (torch đã có sẵn trong base image)
COPY builder/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Tải & BAKE model vào image → không tải lúc chạy → cold-start nhanh
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('k2-fsa/OmniVoice')"

# Chạy hoàn toàn offline lúc runtime (model đã có trong image)
ENV HF_HUB_OFFLINE=1
ENV TRANSFORMERS_OFFLINE=1

COPY src/handler.py /handler.py
CMD ["python", "-u", "/handler.py"]
