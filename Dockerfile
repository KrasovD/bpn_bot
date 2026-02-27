FROM python:3.12-slim-trixie


WORKDIR /app

RUN uv sync

# Теперь код
COPY . .

# Чтобы логи сразу шли в stdout без буфера
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["uv", "run", "app.main"]