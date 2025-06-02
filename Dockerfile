FROM python:3.10-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user to run the application
RUN useradd -m discbot && \
    chown -R discbot:discbot /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_DIR=/app/data

# Create data directory and set permissions
RUN mkdir -p /app/data && \
    chown -R discbot:discbot /app/data

# Switch to non-root user
USER discbot

# Run the bot
CMD ["python", "main.py"]