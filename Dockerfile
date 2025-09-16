# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install "poetry==1.4.2"

# Copy the entire project code
COPY . .

# Configure poetry to not create a virtual environment in the container
RUN poetry config virtualenvs.create false

# Install project dependencies
RUN poetry install --only main --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# Now perform a full poetry install to include the project and its dependencies like uvicorn
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Poetry
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
