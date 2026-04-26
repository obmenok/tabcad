FROM python:3.11-slim

# Install system deps for matplotlib/Pillow
RUN apt-get update && apt-get install -y \
    build-essential \
    libfreetype6-dev \
    libpng-dev \
    fonts-liberation \
    libglib2.0-0 \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgtk-3-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV MPLBACKEND=Agg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8050

# 2 workers for 4 GB VPS.
# Access log is intentionally disabled to keep container logs focused on app diagnostics.
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8050", "--timeout", "120", "--error-logfile", "-", "--capture-output", "--log-level", "info", "app:server"]
