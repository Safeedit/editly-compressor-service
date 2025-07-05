# Base image
FROM python:3.11-slim

# Install Ghostscript
RUN apt-get update && apt-get install -y \
    ghostscript \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask port
EXPOSE 10000

# Run the app
CMD ["python", "app.py"]
