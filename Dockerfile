# Use the official Playwright image which comes with Python and Browsers pre-installed
# This avoids the "missing dependencies" nightmare on Linux
# FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy
# Set working directory
WORKDIR /app

# Upgrade system packages to fix OS-level vulnerabilities (e.g., gpg CVE-2025-68973)
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and setuptools to ensure smooth installation
# Then install dependencies
# Finally, uninstall setuptools to remove the bundled jaraco.context vulnerability (GHSA-58pv-8j8x-9vj2)
# as it is a build-time dependency not required for runtime.
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt && \
    pip uninstall -y setuptools

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Set environment variable to indicate Production
ENV ENV=production

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
