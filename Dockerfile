FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN uv sync --locked
# Теперь код
COPY . .

# Чтобы логи сразу шли в stdout без буфера
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["uv", "run", "app.main"]