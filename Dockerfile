# Use the official, lightweight Python 3.11 image
FROM python:3.11-slim

# Create a non-root user and group for enterprise security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list and install without caching junk files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and grant ownership to the non-root user
COPY . .
RUN chown -R appuser:appgroup /app

# Switch execution to the non-root user
USER appuser

# Expose port 8080 (Required by Google Cloud Run)
EXPOSE 8080

# Command to start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]