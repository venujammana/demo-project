# Use an official Python runtime as a parent image
FROM python:3.10-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the application will run on
# Cloud Run typically expects services to listen on the PORT environment variable,
# which defaults to 8080.
EXPOSE 8080

# Define environment variables
ENV FLASK_APP=app.py
ENV PORT=8080

# Run the app.py when the container launches
# Use gunicorn for a production-ready WSGI server
# gunicorn --bind :$PORT --workers 1 --threads 8 app:app
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
