FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . .

RUN uv sync --locked

# Чтобы логи сразу шли в stdout без буфера
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["uv", "run", "python", "-m", "app.main"]