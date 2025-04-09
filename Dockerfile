FROM python:3.9-slim

# Install FFmpeg and other system dependencies, output to build logs with minimal overhead
RUN apt-get update -qq && apt-get install -y --no-install-recommends ffmpeg && \
    echo "FFmpeg installed successfully" || (echo "FFmpeg installation failed" && exit 1) && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Update pip to the latest version with quiet output
RUN pip install --upgrade pip -q && echo "Pip upgraded successfully" || (echo "Pip upgrade failed" && exit 1)

# Set working directory
WORKDIR /app

# Copy requirements.txt and install Python dependencies with minimal output
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -q && echo "Python dependencies installed successfully" || (echo "Failed to install Python dependencies" && exit 1)

# Copy all files and debug directory contents to build logs
COPY . .
RUN echo "Files in /app after COPY:" && ls -la /app || echo "Failed to list files"

# Check for uploader.py and set fallback script if not found, output to build logs
RUN if [ ! -f uploader.py ]; then \
    echo "Warning: uploader.py not found, checking for alternatives" && \
    for file in *.py; do [ -f "$file" ] && export PYTHON_SCRIPT="$file" && break; done && \
    if [ -z "$PYTHON_SCRIPT" ]; then echo "Error: No Python script found" && exit 1; else echo "Found alternative script: $PYTHON_SCRIPT"; fi; \
    fi

# Create a directory for logs with minimal permissions and ensure it’s writable
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Command to run the script with logging to file and stdout, appending logs
CMD ["sh", "-c", "echo 'Starting script execution: $(date)' >> /app/logs/runtime.log 2>/dev/null && \
     echo 'Starting script execution: $(date)' && \
     if [ -n \"$PYTHON_SCRIPT\" ]; then python $PYTHON_SCRIPT >> /app/logs/runtime.log 2>&1; else python uploader.py >> /app/logs/runtime.log 2>&1; fi && \
     echo 'Script execution completed: $(date)' >> /app/logs/runtime.log 2>/dev/null && \
     echo 'Script execution completed: $(date)' && \
     cat /app/logs/runtime.log /app/deployment.log /app/deployment_diagnostics.log >> /app/combined_logs.log 2>/dev/null || echo 'Failed to combine logs'"]

# Optional: Health check (commented out, enable if needed)
# HEALTHCHECK --interval=30s --timeout=3s \
#   CMD curl -f http://localhost/ || exit 1
