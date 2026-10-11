FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
RUN pip install --no-cache-dir uv

# Dependencies first: this layer is reused while only the code changes.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev

# The app only reads /app at runtime, so a non-root user needs no chown (and no extra layer).
RUN useradd --create-home --uid 10001 resonance
USER resonance

EXPOSE 8000

# Every start (all steps idempotent): migrations, then reference data and the admin from
# ADMIN_EMAIL/ADMIN_PASSWORD; SEED_DEMO=true adds demo accounts. --proxy-headers takes the
# client address from nginx / Vercel / Render X-Forwarded-For, which the per-IP rate limits
# depend on. PORT is set by Render; local/compose default to 8000.
CMD ["sh", "-c", "alembic upgrade head && if [ \"$SEED_DEMO\" = \"true\" ]; then python -m app.seed --demo; else python -m app.seed; fi && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=\"${FORWARDED_ALLOW_IPS:-*}\""]
