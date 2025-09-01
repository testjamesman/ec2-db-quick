# Base image
FROM python:3.12-slim

# Install build-essential, which contains the C/C++ compilers (like gcc)
# needed to build the asyncpg package from source.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up the application directory
WORKDIR /app

# Copy dependency files and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port and run the application
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
