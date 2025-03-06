# Use the official Python image from the DockerHub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application into the container
COPY . .

# Expose the port that the Flask app will run on
EXPOSE 5000

# Define the command to run the app
CMD ["python", "app.py"]