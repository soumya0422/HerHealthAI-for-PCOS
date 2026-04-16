FROM python:3.11-slim

# Set up a new user named "user" with user id 1000
RUN useradd -m -u 1000 user

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files with proper ownership
COPY --chown=user . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV HOME=/home/user
ENV PATH=/home/user/.local/bin:$PATH

# Switch to the non-root user
USER user

# Expose the Hugging Face default port
EXPOSE 7860

# Start FastAPI application on port 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
