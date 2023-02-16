# Base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port on which the application is running
EXPOSE 8080

# Start the application
CMD ["uvicorn", "main:app","--reload", "--host 0.0.0.0","--port 8080"]
