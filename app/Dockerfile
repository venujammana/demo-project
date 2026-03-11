# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install any needed packages specified in requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port that the app will run on
# Cloud Run typically expects port 8080, which is automatically set by the environment variable PORT
# However, for local testing, or explicit clarity, we expose it.
EXPOSE 8080

# Run gunicorn to serve the Flask application
# The `PORT` environment variable is automatically supplied by Cloud Run.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
