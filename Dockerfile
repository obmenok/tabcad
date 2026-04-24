FROM python:3.11-slim

# Install system deps for matplotlib/Pillow
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

# 2 workers for 4 GB VPS, with access logs enabled for callback debugging
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8050", "--timeout", "120", "--access-logfile", "-", "app:server"]