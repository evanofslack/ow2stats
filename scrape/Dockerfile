# Use a slim Python base image
FROM python:3.13-slim

# Set the working directory
WORKDIR /app

# Install uv for fast package installation
RUN pip install uv

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync

# Copy the rest of the application code
COPY . .

# Set the command to run the scraper
CMD ["python", "-u", "scrape.py"]
