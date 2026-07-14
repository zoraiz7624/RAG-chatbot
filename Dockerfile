FROM python:3.10-slim

# ---- System dependencies ----
# build-essential + cmake: needed if/when you add face_recognition (dlib)
# espeak-ng: needed by pyttsx3 for text-to-speech
# ffmpeg: needed by faster-whisper / audio handling
# libgl1: needed by dlib/face_recognition + opencv if used
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    espeak-ng \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- Python dependencies ----
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---- App code ----
COPY . .

# HF Spaces requires writable dirs at /app and listening on port 7860
RUN mkdir -p /app/replies /app/rag_doc /app/vector_db && \
    chmod -R 777 /app/replies /app/rag_doc /app/vector_db

# Pre-download the whisper + embedding models at BUILD time so the
# container doesn't stall downloading them on first request
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"
RUN python -c "from langchain_community.embeddings import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')"

EXPOSE 7860

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
