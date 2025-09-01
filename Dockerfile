# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir: Disables the cache, which is useful for keeping image sizes small
# --upgrade pip: Upgrades pip to the latest version
RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define the command to run the application
# Use --host 0.0.0.0 to make the app accessible from outside the container
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
