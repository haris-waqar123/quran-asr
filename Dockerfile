# Use the official Python 3.10.11 image from the Docker Hub
FROM python:3.10.11-slim

# Set the working directory
WORKDIR /ASR_LIVE

# Install virtual environment and other dependencies
# RUN apt-get update && apt-get install -y python3-venv

# Create and activate the virtual environment
RUN python3 -m venv venv
RUN . venv/bin/activate

# # Copy the requirements file into the Docker image
COPY . .
# COPY requirements.txt .

# Install the dependencies
RUN pip install torch==2.3.1 torchvision==0.18.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cu118
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["./venv/bin/python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
