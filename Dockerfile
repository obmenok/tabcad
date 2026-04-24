FROM python:3.11-slim

# Установка системных зависимостей для matplotlib/Pillow
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV MPLBACKEND=Agg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# Для VPS 4 GB RAM используем 2 воркера
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8050", "--timeout", "120", "app:app"]