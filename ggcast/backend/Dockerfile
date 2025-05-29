# ggcast/backend/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy only pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
