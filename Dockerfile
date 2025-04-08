FROM python:3.9-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly copy the Python script
COPY AIVideoCreatorYoutubeUploader.py .

# Copy any other necessary files
COPY video_counts.json .

# Command to run the script
CMD ["python", "AIVideoCreatorYoutubeUploader.py"]
