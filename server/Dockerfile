# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server directory
COPY server/ ./server/

# Copy the shared database if necessary, or just rely on mount
# Expose the correct port
EXPOSE 55555

# Define environment variable
ENV HOST=0.0.0.0
ENV PORT=55555

# Change to server directory where server.py resides
WORKDIR /app/server

# Run the socket IO server
CMD ["python", "server.py"]
