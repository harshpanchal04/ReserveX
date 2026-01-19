# ReserveX (Train Surfer)

ReserveX (also known as Train Surfer) is a powerful Python-based tool designed to help Indian Railways passengers find vacant seats on trains when direct tickets are unavailable. It leverages advanced web scraping and algorithmic optimization to discover "hidden" vacancies and construct "Hacker Chains"—optimal seat-hopping itineraries that cover the entire journey.

## 🚀 Key Features

*   **Smart Vacancy Scanning**: Uses **Playwright** to intercept internal IRCTC APIs (`coachComposition`), allowing it to scan every coach (S1, S2, B1, etc.) for partial vacancies that are often invisible on standard booking portals.
*   **Hacker Chain Algorithm**: A greedy algorithm that stitches together multiple partial vacancies to create a complete journey. It minimizes seat swaps to ensure maximum comfort.
*   **Visual Timeline**: A beautiful, interactive visual representation of your journey, showing exactly where you need to swap seats and what the intermediate stations are.
*   **PDF Ticket Generation**: Generates a professional-looking PDF itinerary for your "Hacker Chain" or single seat, ready for offline reference.
*   **Comfort Filters**: Filter results by berth type (Lower, Side Lower, AC, etc.) to find the most comfortable option.
*   **Robust & Stealthy**: Implements "Fake Headless" browsing and other stealth techniques to bypass anti-bot protections and ensure reliable data fetching.

## 🛠️ Technical Architecture

### 1. Route Discovery (`scraper.py`)
*   **Function**: `get_train_route(train_no)`
*   **Logic**: Launches a browser instance to scrape the official station list and distances for the given train.
*   **Fallback**: Includes hardcoded fallback data for popular trains (e.g., Karnataka Express) to ensure functionality even if the route page is slow or unresponsive.

### 2. Vacancy Scanning (`scraper.py`)
*   **Function**: `scan_vacancies(...)`
*   **Technique**: API Interception. Instead of scraping the DOM (which is slow and brittle), the tool intercepts the `coachComposition` JSON response from the server.
*   **Data Extracted**: Coach number, Berth number, Berth type (LB, UB, etc.), and the specific "From" and "To" stations for each vacant segment.

### 3. Optimization Engine (`solver.py`)
*   **Single Seat Optimization**: Filters vacancies based on user preferences (AC only, Lower Berth only) and sorts them by coverage distance.
*   **Hacker Chain Logic**:
    1.  Identifies all "Starting Seats" that cover the boarding station.
    2.  Uses a **Greedy Algorithm** to find the next best seat that overlaps with the current seat and extends the journey furthest towards the destination.
    3.  Repeats until the destination is reached or no valid connection is found.

### 4. User Interface (`app.py`)
*   Built with **Streamlit** for a responsive and interactive web-based UI.
*   Manages session state to persist data between reruns (route data, scan results).
*   Integrates `matplotlib` (implied) or custom HTML/CSS for visual timelines.

## 📦 Installation

### Prerequisites
*   **Python 3.8+**
*   **Google Chrome** (or Chromium) installed on your system.

### Setup
1.  **Clone the Repository**
    ```bash
    git clone https://github.com/harshpanchal04/ReserveX.git
    cd ReserveX
    ```

2.  **Create a Virtual Environment** (Recommended)
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright Browsers**
    ```bash
    playwright install chromium
    ```

## 🖥️ Usage

1.  **Run the Application**
    ```bash
    streamlit run app.py
    ```

2.  **Workflow**
    *   **Step 1**: Enter the **Train Number** (e.g., 12627) and **Journey Date** in the sidebar. Click "Fetch Route".
    *   **Step 2**: Select your **Boarding** and **Destination** stations from the main dropdowns.
    *   **Step 3**: Click "Find Seats". The tool will open a browser (in the background or visible if Developer Mode is on) and scan the train.
    *   **Step 4**: View the results!
        *   **Best Single Seat**: The longest continuous seat available.
        *   **Hacker Chain**: A combination of seats to cover the full trip.
    *   **Step 5**: Download your **PDF Ticket** for easy reference.

## 🔄 CI/CD Pipeline

This project implements a production-grade **DevSecOps** pipeline using GitHub Actions.

### 1. Continuous Integration (CI)
Every push to `master` triggers:
-   **Linting**: `flake8` checks for code style compliance.
-   **Security Scans**:
    -   **SAST**: `bandit` scans Python code for vulnerabilities.
    -   **SCA**: `safety` checks dependencies for known CVEs.
-   **Unit Tests**: `pytest` validates core logic (mocking external APIs).
-   **Containerization**: Builds a Docker image.
-   **Image Scanning**: `trivy` scans the Docker image for OS/library vulnerabilities.
-   **Registry Push**: Pushes safe images to DockerHub.

### 2. Continuous Deployment (CD)
Automated deployment to Kubernetes:
-   **Staging**: Deploys to `staging` namespace -> Runs **DAST** (OWASP ZAP).
-   **Production**: Deploys to `production` namespace (Requires Manual Approval).

[![CI Status](https://github.com/harshpanchal04/ReserveX/actions/workflows/ci.yml/badge.svg)](https://github.com/harshpanchal04/ReserveX/actions/workflows/ci.yml)

## 📂 File Structure

*   `app.py`: Main Streamlit application entry point.
*   `scraper.py`: Core logic for browser automation and data extraction using Playwright.
*   `solver.py`: Algorithms for processing raw vacancy data and finding optimal chains.
*   `utils.py`: Helper functions for PDF generation (`fpdf`) and HTML visualization.
*   `vacancy_finder.py`: A standalone CLI version of the tool (useful for testing/debugging without UI).
*   `requirements.txt`: List of Python dependencies.

## ⚠️ Disclaimer

This tool is for **informational purposes only**. It helps you find available seats, but it **does not book tickets**. You must book the corresponding segments on the official IRCTC website or app. Use responsibly and adhere to IRCTC's terms of service.
