FROM python:3.11-slim

# Системные зависимости (минимум)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

RUN uv sync

# Теперь код
COPY . .

# Чтобы логи сразу шли в stdout без буфера
ENV PYTHONUNBUFFERED=1

# Запуск
CMD ["uv", "run", "app.main"]