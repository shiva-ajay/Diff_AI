# --- Stage 1: Build dependencies ---
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies required for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install a specific version of Poetry using the official installer
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - --version "1.7.1"

# Copy only the files needed for dependency installation
COPY pyproject.toml poetry.lock ./

# Add a step to update the 'packaging' library to avoid canonicalize_version() error
# This ensures compatibility with the latest setuptools
RUN poetry run pip install --upgrade packaging

# Configure poetry and install dependencies only, without the project code itself
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root


# --- Stage 2: Final production image ---
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy Poetry's installation from the builder stage
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
COPY --from=builder $POETRY_HOME $POETRY_HOME

# Copy the system libraries installed in the builder stage
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy the application source code
COPY . .

# Now perform a full poetry install to include the project and its dependencies like uvicorn
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application using Poetry
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
