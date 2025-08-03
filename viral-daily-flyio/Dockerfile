FROM python:3.11-slim

WORKDIR /app

# Copy and install Python requirements
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY backend/ .

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["python", "server.py"]
