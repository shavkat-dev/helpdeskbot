# syntax=docker/dockerfile:1
# Dockerfile

# 1. Base Image
# We start with a slim, official Python image. This keeps our image size small.
# Using a specific version (e.g., 3.9) is good practice for reproducibility.
FROM python:3.9-slim

# 2. Set the working directory inside the container
# This is where our application code will live.
WORKDIR /app

# 3. Copy dependencies file and install them
# We copy only the requirements file first to leverage Docker's layer caching.
# If requirements.txt doesn't change, Docker won't re-run this layer, speeding up builds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the application code into the container
# This copies the rest of the source code into the /app directory.
COPY . .

# 5. Command to run the application
# This is the command that will be executed when the container starts.
# It launches the bot by importing and starting the 'updater'.
CMD ["python", "-c", "from main import updater; updater.start_polling()"]
