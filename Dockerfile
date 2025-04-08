FROM python:3.9-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files and verify
COPY *.py .
RUN echo "Files in /app after COPY *.py:" > /app/build_log.txt && ls -la >> /app/build_log.txt

# Copy any other necessary files
COPY video_counts.json .

# Debug runtime file check
CMD ["sh", "-c", "ls -la /app && python /app/AIVideoCreatorYoutubeUploader.py"]
