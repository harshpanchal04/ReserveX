# 🚂 ReserveX (Train Surfer)

[![CI Pipeline](https://github.com/harshpanchal04/ReserveX/actions/workflows/ci.yml/badge.svg)](https://github.com/harshpanchal04/ReserveX/actions/workflows/ci.yml)
[![CD Pipeline](https://github.com/harshpanchal04/ReserveX/actions/workflows/cd.yml/badge.svg)](https://github.com/harshpanchal04/ReserveX/actions/workflows/cd.yml)
[![Docker Image](https://img.shields.io/docker/v/harshpanchal04/reservex?label=DockerHub&logo=docker)](https://hub.docker.com/r/harshpanchal04/reservex)

**ReserveX** is a Python-based tool that helps Indian Railways passengers find vacant seats when direct tickets are unavailable. It discovers "hidden" vacancies and constructs **Hacker Chains**—optimal seat-hopping itineraries that cover your entire journey.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **Smart Vacancy Scanning** | Intercepts IRCTC's internal `coachComposition` API to find partial vacancies |
| 🔗 **Hacker Chain Algorithm** | Greedy algorithm that stitches multiple partial vacancies into a complete journey |
| 📊 **Visual Timeline** | Interactive visualization showing exactly where to swap seats |
| 📄 **PDF Generation** | Downloadable itinerary for offline reference |
| ⚙️ **Stealth Mode** | Fake-headless browsing to bypass anti-bot protections |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Chrome or Chromium

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/harshpanchal04/ReserveX.git
cd ReserveX

# 2. Create virtual environment
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Run the application
streamlit run app.py
```

### Using Docker

```bash
# Pull the image
docker pull harshpanchal04/reservex:latest

# Run the container
docker run -p 8501:8501 harshpanchal04/reservex:latest

# Access at http://localhost:8501
```

---

## 🛠️ Technical Architecture

### Core Components

| File | Purpose |
|------|---------|
| `app.py` | Streamlit web application entry point |
| `scraper.py` | Playwright browser automation & API interception |
| `solver.py` | Optimization algorithms for seat finding |
| `utils.py` | PDF generation & visualization helpers |
| `Dockerfile` | Container definition (Playwright base image) |

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | Streamlit |
| Backend | Python 3.10 |
| Web Scraping | Playwright |
| Containerization | Docker |
| Orchestration | Kubernetes (K3s) |
| Cloud | AWS EC2 |

---

## 🔄 CI/CD Pipeline

This project implements a production-grade **DevSecOps** pipeline using GitHub Actions.

### Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     CI PIPELINE (10 Stages)                 │
├─────────────────────────────────────────────────────────────┤
│ Checkout → Setup → Lint → SAST → SCA → Test → Build →     │
│ Smoke Test → Image Scan → Push to Registry                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     CD PIPELINE (5 Stages)                  │
├─────────────────────────────────────────────────────────────┤
│ SSH Connect → Bootstrap K3s → Apply Manifests →            │
│ Rolling Update → Health Check                               │
└─────────────────────────────────────────────────────────────┘
```

### CI Stages

| Stage | Tool | Purpose |
|-------|------|---------|
| **Linting** | Flake8 | PEP8 code style compliance |
| **SAST** | CodeQL | Static security analysis |
| **SCA** | OWASP Dependency Check | Dependency vulnerability scanning |
| **Unit Tests** | Pytest | Functional testing |
| **Smoke Test** | curl | Container startup verification |
| **Image Scan** | Trivy | Container vulnerability scanning |

### CD Stages

| Stage | Tool | Purpose |
|-------|------|---------|
| **SSH Connect** | appleboy/ssh-action | Remote server access |
| **Bootstrap** | K3s installer | Kubernetes installation (if needed) |
| **Apply Manifests** | kubectl | Deploy to Kubernetes |
| **Health Check** | curl | Production verification |

📖 **Detailed architecture documentation**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 🔐 Secrets Configuration

Configure these secrets in **GitHub Repository Settings → Secrets → Actions**:

| Secret Name | Description | How to Obtain |
|-------------|-------------|---------------|
| `DOCKERHUB_USERNAME` | DockerHub username | Your DockerHub account username |
| `DOCKERHUB_TOKEN` | DockerHub access token | DockerHub → Account Settings → Security → New Access Token |
| `EC2_HOST` | EC2 public IP address | AWS Console → EC2 → Instances → Public IPv4 |
| `EC2_SSH_KEY` | SSH private key content | Content of your `.pem` file (including headers) |

---

## 📁 Project Structure

```
ReserveX/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI pipeline definition
│       └── cd.yml              # CD pipeline definition
├── docs/
│   ├── ARCHITECTURE.md         # Visual architecture documentation
│   └── K8S_SETUP.md           # Kubernetes setup guide
├── k8s/
│   ├── deployment.yaml         # K8s Deployment manifest
│   └── service.yaml            # K8s Service manifest
├── tests/
│   └── test_solver.py          # Unit tests for solver.py
├── app.py                      # Streamlit application
├── scraper.py                  # Playwright automation
├── solver.py                   # Optimization algorithms
├── utils.py                    # Helper functions
├── Dockerfile                  # Container definition
├── requirements.txt            # Python dependencies
├── PROJECT_REPORT.md           # Detailed project report
└── README.md                   # This file
```

---

## 🖥️ Usage Guide

1. **Enter Train Details**: Input the train number (e.g., 12627) and journey date
2. **Fetch Route**: Click "Fetch Route" to load station list
3. **Select Stations**: Choose boarding and destination stations
4. **Find Seats**: Click "Find Seats" to scan for vacancies
5. **View Results**:
   - **Best Single Seat**: Longest continuous seat available
   - **Hacker Chain**: Combination of seats covering full trip
6. **Download PDF**: Save your itinerary for reference

---

## 🌐 Accessing the Deployed Application

Once CD pipeline completes successfully:

```
http://<EC2-PUBLIC-IP>:30001
```

Replace `<EC2-PUBLIC-IP>` with your EC2 instance's public IPv4 address.

---

## ⚠️ Disclaimer

This tool is for **informational purposes only**. It helps you find available seats, but it **does not book tickets**. You must book the corresponding segments on the official IRCTC website or app. Use responsibly and adhere to IRCTC's terms of service.

---

## 📄 License

This project is for educational purposes as part of an Advanced DevOps course.

---

*Built with ❤️ using Python, Streamlit, and Kubernetes*
