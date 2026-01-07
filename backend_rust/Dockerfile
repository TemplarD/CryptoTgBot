FROM rust:1.85-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-dev \
    python3.13-venv \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование манифеста
COPY Cargo.toml Cargo.lock ./

# Создание пустого src для кэширования зависимостей
RUN mkdir src && echo "fn main() {}" > src/main.rs

# Установка зависимостей (кэшируется)
RUN cargo build --release && rm -rf src

# Копирование исходного кода
COPY src ./src

# Сборка проекта
RUN cargo build --release

# Финальный образ
FROM debian:bookworm-slim

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    python3.13 \
    python3.13-venv \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование скомпилированной библиотеки
COPY --from=builder /app/target/release/libcrypto_core.so .
COPY --from=builder /app/target/release/deps .

# Переменные окружения
ENV LD_LIBRARY_PATH=/app
ENV PYTHONPATH=/app

# Команда по умолчанию
CMD ["python3.13", "-c", "import crypto_core; print('Rust core loaded successfully')"]
