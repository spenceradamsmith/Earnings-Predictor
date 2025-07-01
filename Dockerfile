# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code (including catboost_model.cbm)
COPY . .

# Expose the port EB will use
EXPOSE 5000

# Run Gunicorn against your app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
