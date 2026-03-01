FROM python:3.12-slim

WORKDIR /app

# 1) Install dependencies (cached unless pyproject.toml changes)
COPY pyproject.toml .
RUN mkdir -p alphaa && touch alphaa/__init__.py \
    && pip install --no-cache-dir . \
    && rm -rf alphaa

# 2) Copy source and install package (fast — deps already cached)
COPY alphaa/ alphaa/
RUN pip install --no-cache-dir --no-deps .

EXPOSE 8000
CMD ["uvicorn", "alphaa.web.app:create_app", "--host", "0.0.0.0", "--port", "8000"]
