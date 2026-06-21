FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    PIP_NO_CACHE_DIR=1 \
    TSP_WORKERS=4 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1

COPY requirements.txt pyproject.toml README.md ./
COPY src ./src
COPY data ./data
COPY experiments ./experiments
COPY scripts ./scripts

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -e . \
    && mkdir -p results

# Quick smoke test by default; override with docker compose or docker run
CMD ["python", "-u", "experiments/run_comparison.py", "--quick", "--workers", "4"]
