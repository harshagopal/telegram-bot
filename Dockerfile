FROM python:3.9-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files as a fallback, then explicitly verify the script
COPY . .
RUN if [ ! -f AIVideoCreatorYoutubeUploader.py ]; then echo "Error: AIVideoCreatorYoutubeUploader.py not found" && exit 1; fi
RUN echo "Files in /app after COPY:" > /app/build_log.txt && ls -la >> /app/build_log.txt

# Copy any other necessary files (redundant but ensures presence)
COPY video_counts.json .

# Command to run the script
CMD ["python", "AIVideoCreatorYoutubeUploader.py"]
