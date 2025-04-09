FROM python:3.9-slim

# Install FFmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files and debug directory contents to stdout
COPY . .
RUN echo "Files in /app after COPY:" && ls -la

# Check for uploader.py and set fallback script if not found
RUN if [ ! -f uploader.py ]; then \
    echo "Warning: uploader.py not found, checking for alternatives" && \
    for file in *.py; do [ -f "$file" ] && export PYTHON_SCRIPT="$file" && break; done && \
    if [ -z "$PYTHON_SCRIPT" ]; then echo "Error: No Python script found" && exit 1; else echo "Found alternative script: $PYTHON_SCRIPT"; fi; \
    fi

# Command to run the script (use detected script if fallback triggered)
CMD ["sh", "-c", "if [ -n \"$PYTHON_SCRIPT\" ]; then python $PYTHON_SCRIPT; else python uploader.py; fi"]
