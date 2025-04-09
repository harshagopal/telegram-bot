FROM python:3.9-slim

# Install FFmpeg and other system dependencies, output to build logs
RUN apt-get update && apt-get install -y ffmpeg && echo "FFmpeg installed successfully" || (echo "FFmpeg installation failed" && exit 1) && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN pip install --upgrade pip && echo "Pip upgraded successfully" || (echo "Pip upgrade failed" && exit 1)

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies with detailed logging
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && echo "Python dependencies installed successfully" || (echo "Failed to install Python dependencies" && exit 1)

# Copy all files and debug directory contents to build logs
COPY . .
RUN echo "Files in /app after COPY:" && ls -la || echo "Failed to list files"

# Check for uploader.py and set fallback script if not found, output to build logs
RUN if [ ! -f uploader.py ]; then \
    echo "Warning: uploader.py not found, checking for alternatives" && \
    for file in *.py; do [ -f "$file" ] && export PYTHON_SCRIPT="$file" && break; done && \
    if [ -z "$PYTHON_SCRIPT" ]; then echo "Error: No Python script found" && exit 1; else echo "Found alternative script: $PYTHON_SCRIPT"; fi; \
    fi

# Command to run the script with logging
CMD ["sh", "-c", "echo 'Starting script execution: $(date)' && if [ -n \"$PYTHON_SCRIPT\" ]; then python $PYTHON_SCRIPT; else python uploader.py; fi && echo 'Script execution completed: $(date)'"]
