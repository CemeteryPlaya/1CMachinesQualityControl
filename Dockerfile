FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY app_routes.py .
COPY bot_handlers.py .
COPY bot_instance.py .
COPY database.py .
COPY form_config.py .
COPY odata_service.py .
COPY sheets_service.py .
COPY translations.py .
COPY tbot-checklists-b26f4a92ff19.json .
COPY static/ ./static/
COPY templates/ ./templates/

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')"

# Run application
CMD ["python", "main.py"]
