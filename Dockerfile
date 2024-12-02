# Use Python 3.10 base image
FROM python:3.10-alpine as base

# Set environment variables to disable buffering and bytecode creation
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory for the app
WORKDIR /app

# Install system dependencies
RUN apk --update add \
    build-base \
    postgresql-dev \
    python3-dev \
    libpq \
    jpeg-dev \
    zlib-dev \
    musl-dev \
    gcc \
    libffi-dev \
    bash

# Copy the requirements and install them
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . /app/

# Copy and make entrypoint script executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose port 8000 for the app
EXPOSE 8000

# Set the entrypoint to your script
ENTRYPOINT ["/entrypoint.sh"]