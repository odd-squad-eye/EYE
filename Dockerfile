# Lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV / YOLO
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a dummy flash_attn stub so transformers' import scanner
# doesn't reject Florence-2's modeling file on CPU-only containers.
# The actual flash-attention code path is never used (we set attn_implementation="eager").
RUN mkdir -p /usr/local/lib/python3.11/site-packages/flash_attn && \
    echo "# stub – satisfies import check only" > /usr/local/lib/python3.11/site-packages/flash_attn/__init__.py && \
    echo "" > /usr/local/lib/python3.11/site-packages/flash_attn/bert_padding.py && \
    echo "def flash_attn_varlen_func(*a,**k): raise NotImplementedError('flash_attn stub')" > /usr/local/lib/python3.11/site-packages/flash_attn/flash_attn_interface.py

# Copy project files
COPY . .

# Expose port
ENV PORT=7860
EXPOSE 7860

# Run FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
