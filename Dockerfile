FROM python:3.9-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files and debug directory contents
COPY . .
RUN echo "Files in /app after COPY:" > /app/build_log.txt && ls -la >> /app/build_log.txt
RUN if [ ! -f AIVideoCreatorYoutubeUploader.py ]; then \
    echo "Warning: AIVideoCreatorYoutubeUploader.py not found, checking for alternatives" && \
    for file in *.py; do [ -f "$file" ] && export PYTHON_SCRIPT=$file && break; done && \
    [ -z "$PYTHON_SCRIPT" ] && echo "Error: No Python script found" && exit 1 || echo "Found alternative script: $PYTHON_SCRIPT"; \
    fi

# Command to run the script (use detected script if fallback triggered)
CMD ["sh", "-c", "if [ -n \"$PYTHON_SCRIPT\" ]; then python $PYTHON_SCRIPT; else python AIVideoCreatorYoutubeUploader.py; fi"]
