# Base image
FROM python:3.13-slim

# Set environment variables to prevent interactive prompts
ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies: curl for downloading, gnupg for key management,
# and unixodbc-dev for the Python driver to link against.
RUN apt-get update && apt-get install -y curl gnupg unixodbc-dev

# Add Microsoft's official repository for the ODBC driver using the modern, secure method
# 1. Download the Microsoft GPG key
# 2. Convert the key to the new format and place it in the trusted keyrings directory
# 3. Add the repository configuration
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list

# Update the package list again and install the ODBC driver
RUN apt-get update && apt-get install -y msodbcsql18

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
