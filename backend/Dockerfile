# Production image for the FastAPI backend
FROM python:3.12-slim

# Faster, quieter Python in containers
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app and the startup script
COPY . .
RUN chmod +x start.sh

EXPOSE 8000

# Railway/Heroku inject $PORT; migrations run before startup
CMD ["./start.sh"]
