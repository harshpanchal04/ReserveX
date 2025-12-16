# Use the official Playwright image which comes with Python and Browsers pre-installed
# This avoids the "missing dependencies" nightmare on Linux
# FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy
# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Set environment variable to indicate Production
ENV ENV=production

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
