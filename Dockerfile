# Use Python 3.10 base image
FROM python:3.10-alpine as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk --update add --no-cache \
    build-base \
    postgresql-dev \
    python3-dev \
    libpq \
    jpeg-dev \
    zlib-dev \
    musl-dev \
    gcc \
    libffi-dev \
    bash \
    gettext && \
    adduser -D -h /app -u 1000 appuser

# Ensure staticfiles directory exists with correct permissions
RUN mkdir -p /app/staticfiles && \
    chmod -R 755 /app/staticfiles && \
    chown -R appuser:appuser /app/staticfiles

# Copy requirements and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Use a non-root user
USER appuser

# Expose port for application
EXPOSE 8000

# Healthcheck to verify container health
HEALTHCHECK CMD curl --fail http://localhost:8000/health/ || exit 1

# Entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
