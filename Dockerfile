# ML-Server-Recommedations — Flask API
# Runs the /recommendation endpoint that serves pipeline-generated CSVs.
# The pipeline (run_all.py) is a separate Container Apps Job; this image
# only needs to serve the API.

FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# System deps for pandas/numpy/scipy/scikit-learn
RUN --mount=target=/var/lib/apt/lists,type=cache,sharing=locked \
    --mount=target=/var/cache/apt,type=cache,sharing=locked \
    rm -f /etc/apt/apt.conf.d/docker-clean && \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libgomp1 \
    && apt-get clean

WORKDIR /app

# Install Python dependencies first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY API2.py Saving_recom.py Merging.py Fetch_params.py recom7_2.py run_all.py ./
COPY feature_columns.json google-ads.yaml ./

# Create data directories — DATA_DIR defaults to /app/data in the container.
# Mount a persistent volume here so the pipeline's output survives restarts.
RUN mkdir -p /app/data /app/input_params

# Non-root user for security
RUN addgroup --system mlapi && adduser --system --ingroup mlapi mlapi \
    && chown -R mlapi:mlapi /app
USER mlapi

EXPOSE 5000

# Gunicorn for production; falls back gracefully if not installed.
# flask is always present (in requirements.txt), gunicorn is recommended.
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "API2:app"]
