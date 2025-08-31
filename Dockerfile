# Use official Python image
FROM python:3.10-slim

# Prevent .pyc files and ensure real-time logs
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the full project
COPY . .

# Expose Django port
EXPOSE 8000

# Start Gunicorn WSGI server for production
CMD ["gunicorn", "expenseManager_BE.wsgi:application", "--bind", "0.0.0.0:8000"]
