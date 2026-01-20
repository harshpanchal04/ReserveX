# ReserveX - Advanced DevOps CI/CD Project Report

**Author:** Harsh Panchal  
**Date:** January 20, 2026  
**Repository:** [GitHub - ReserveX](https://github.com/harshpanchal04/ReserveX)

---

## Table of Contents
1. [Problem Background & Motivation](#1-problem-background--motivation)
2. [Application Overview](#2-application-overview)
3. [CI/CD Workflow Diagram](#3-cicd-workflow-diagram)
4. [Pipeline Design & Stages](#4-pipeline-design--stages)
5. [Security & Quality Controls](#5-security--quality-controls)
6. [Results & Observations](#6-results--observations)
7. [Limitations & Improvements](#7-limitations--improvements)
8. [Conclusion](#8-conclusion)

---

## 1. Problem Background & Motivation

### The Challenge
In traditional software development, teams often face the **"It works on my machine"** syndrome. Manual deployments are error-prone, security vulnerabilities go unnoticed, and there's no guarantee that code passing local tests will work in production.

### Why ReserveX Needs CI/CD
ReserveX is a complex web scraping application with several unique challenges:

| Challenge | Risk Without CI/CD | Solution with CI/CD |
|-----------|-------------------|---------------------|
| **Dependency Vulnerabilities** | Python packages may contain CVEs that expose user data | Automated SCA scanning with OWASP Dependency Check |
| **Regression Bugs** | Changes to the "Hacker Chain" algorithm may break seat-finding logic | Unit tests run on every commit via Pytest |
| **Browser Automation Failures** | Playwright may fail silently if browser binaries are missing | Container smoke tests verify startup before deployment |
| **Deployment Inconsistency** | Manual deployment leads to configuration drift | Infrastructure-as-Code with Kubernetes manifests |

### Project Goal
Implement a **production-grade DevSecOps pipeline** that ensures only **clean, secure, and verified** code reaches the production environment—automatically.

---

## 2. Application Overview

### What is ReserveX?
**ReserveX (Train Surfer)** is a Python-based web application that helps Indian Railways passengers find vacant seats when direct tickets are unavailable. It discovers "hidden" vacancies and constructs optimal seat-hopping itineraries called **"Hacker Chains"**.

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Streamlit | Interactive web-based UI |
| **Backend** | Python 3.10 | Core application logic |
| **Web Scraping** | Playwright | Browser automation & API interception |
| **Containerization** | Docker | Consistent runtime environment |
| **Orchestration** | Kubernetes (K3s) | Production deployment & scaling |
| **Cloud** | AWS EC2 | Hosting infrastructure |

### Key Features
- **Smart Vacancy Scanning**: Intercepts IRCTC's internal `coachComposition` API
- **Hacker Chain Algorithm**: Greedy algorithm that stitches partial vacancies
- **Visual Timeline**: Interactive journey visualization
- **PDF Generation**: Downloadable itinerary for offline reference

### Core Files
```
ReserveX/
├── app.py           # Streamlit entry point
├── scraper.py       # Playwright browser automation
├── solver.py        # Optimization algorithms
├── utils.py         # PDF & visualization helpers
├── Dockerfile       # Container definition
└── requirements.txt # Python dependencies
```

---

## 3. CI/CD Workflow Diagram

### Complete Pipeline Architecture

```mermaid
graph TB
    subgraph "Developer"
        A[👨‍💻 Code Push to GitHub]
    end
    
    subgraph "CI Pipeline - GitHub Actions"
        B[1. Checkout Code]
        C[2. Setup Python 3.10]
        D[3. Linting - Flake8]
        E[4. SAST - CodeQL]
        F[5. SCA - OWASP DC]
        G[6. Unit Tests - Pytest]
        H[7. Docker Build]
        I[8. Smoke Test - curl]
        J[9. Image Scan - Trivy]
        K[10. Push to DockerHub]
    end
    
    subgraph "Artifact Registry"
        L[🐳 DockerHub<br/>harshpanchal04/reservex:latest]
    end
    
    subgraph "CD Pipeline - GitHub Actions"
        M[1. SSH to EC2]
        N[2. Bootstrap K3s]
        O[3. Apply Manifests]
        P[4. Rolling Update]
        Q[5. Health Check]
    end
    
    subgraph "AWS Cloud - EC2 Instance"
        subgraph "K3s Kubernetes Cluster"
            R[Pod 1<br/>reservex]
            S[Pod 2<br/>reservex]
            T[Service<br/>NodePort 30001]
        end
    end
    
    subgraph "End Users"
        U[🌐 Internet Users<br/>http://EC2-IP:30001]
    end
    
    A --> B --> C --> D --> E --> F --> G --> H --> I --> J --> K
    K --> L
    L --> M --> N --> O --> P --> Q
    Q --> R
    Q --> S
    T --> R
    T --> S
    U --> T
    
    style A fill:#e1f5ff
    style L fill:#fff4e1
    style R fill:#e8f5e9
    style S fill:#e8f5e9
    style T fill:#f3e5f5
    style U fill:#fce4ec
```

### Security Layers (Shift-Left Approach)

```mermaid
graph LR
    subgraph "Shift-Left Security Pipeline"
        A[📝 Code] --> B[🔍 SAST<br/>CodeQL]
        B --> C[📦 SCA<br/>OWASP DC]
        C --> D[🐳 Container Scan<br/>Trivy]
        D --> E[🧪 Runtime Test<br/>Smoke Test]
        E --> F[✅ Production]
    end
    
    style B fill:#ffcdd2
    style C fill:#f8bbd0
    style D fill:#e1bee7
    style E fill:#d1c4e9
    style F fill:#c8e6c9
```

---

## 4. Pipeline Design & Stages

### 4.1 Continuous Integration (CI)
**File:** `.github/workflows/ci.yml`

| Stage | Tool | Purpose | Why It Matters |
|-------|------|---------|----------------|
| **1. Checkout** | `actions/checkout@v4` | Fetches source code | Required for all subsequent steps |
| **2. Setup** | `actions/setup-python@v4` | Initializes Python 3.10 with pip caching | **Speed**: Caching prevents re-downloading dependencies on every build |
| **3. Linting** | `flake8` | Enforces PEP8 code style | **Quality**: Catches syntax errors and ensures consistent formatting |
| **4. SAST** | `CodeQL` | Static Application Security Testing | **Security**: Detects SQL injection, XSS, and logic vulnerabilities in source code |
| **5. SCA** | `OWASP Dependency Check` | Software Composition Analysis | **Security**: Scans `requirements.txt` against the NVD database for known CVEs |
| **6. Unit Tests** | `pytest` | Functional testing | **Reliability**: Validates the "Hacker Chain" algorithm produces correct results |
| **7. Docker Build** | `docker build` | Container creation | **Consistency**: Packages app with all dependencies |
| **8. Smoke Test** | `curl` | Container startup verification | **Verification**: Ensures the app boots without crashing (catches missing env vars) |
| **9. Image Scan** | `trivy` | Container security scanning | **Security**: Detects OS-level vulnerabilities in the base Playwright image |
| **10. Push** | `docker push` | Registry upload | **Delivery**: Makes the verified image available for deployment |

### 4.2 Continuous Deployment (CD)
**File:** `.github/workflows/cd.yml`

| Stage | Tool | Purpose | Why It Matters |
|-------|------|---------|----------------|
| **1. SSH Connect** | `appleboy/ssh-action` | Remote server access | **Automation**: Eliminates manual server login |
| **2. Bootstrap** | K3s installer script | Kubernetes installation (if missing) | **Self-Healing**: Pipeline works on fresh EC2 instances |
| **3. Apply Manifests** | `kubectl apply` | Kubernetes deployment | **Infrastructure-as-Code**: Declarative configuration |
| **4. Rolling Update** | `kubectl rollout restart` | Zero-downtime deployment | **Availability**: Old pods serve traffic while new ones start |
| **5. Health Check** | `curl` | Production verification | **Validation**: Confirms app is serving traffic on port 30001 |

---

## 5. Security & Quality Controls

### DevSecOps Approach
We implemented a **Shift-Left Security** strategy, integrating security checks at every stage of the pipeline:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SECURITY CHECKPOINT LAYERS                   │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: CODE LEVEL                                            │
│  └── CodeQL: Semantic analysis for Python vulnerabilities       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: DEPENDENCY LEVEL                                      │
│  └── OWASP DC: Scans libraries against CVE database             │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: CONTAINER LEVEL                                       │
│  └── Trivy: Scans OS packages and Python libraries in image    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: RUNTIME LEVEL                                         │
│  └── Smoke Tests: Verifies application starts correctly         │
└─────────────────────────────────────────────────────────────────┘
```

### Secrets Management
All sensitive credentials are stored in **GitHub Secrets** (encrypted at rest):

| Secret | Purpose | Scope |
|--------|---------|-------|
| `DOCKERHUB_USERNAME` | Docker registry authentication | CI Pipeline |
| `DOCKERHUB_TOKEN` | Docker registry authentication | CI Pipeline |
| `EC2_HOST` | Deployment server IP address | CD Pipeline |
| `EC2_SSH_KEY` | SSH private key for server access | CD Pipeline |

### Quality Gates
The pipeline enforces strict quality gates:
- ❌ **Fail on Critical/High Trivy vulnerabilities**
- ❌ **Fail on CodeQL security alerts**
- ⚠️ **Continue with warning on OWASP findings** (for awareness)
- ❌ **Fail if smoke test cannot reach the application**

---

## 6. Results & Observations

### Pipeline Execution Results

| Metric | Value | Observation |
|--------|-------|-------------|
| **CI Duration** | ~3-4 minutes | Acceptable for comprehensive scanning |
| **CD Duration** | ~90 seconds | Fast deployment with K3s |
| **First-Run CD** | ~5 minutes | Includes K3s installation (one-time) |
| **Replicas** | 2 pods | High availability achieved |

### Key Achievements

1. **Automated Security**
   - Every commit is scanned for vulnerabilities before deployment
   - Supply-chain attacks are mitigated via OWASP Dependency Check

2. **Self-Healing Infrastructure**
   - CD pipeline automatically installs K3s if not present
   - Idempotent design allows safe re-runs

3. **Zero-Downtime Deployments**
   - Kubernetes rolling updates ensure continuous availability
   - Old pods only terminate after new pods are healthy

4. **Cost Optimization**
   - K3s uses ~50% less RAM than Minikube
   - Single EC2 t2.micro instance handles full cluster

### Evidence of Success
- ✅ CI Pipeline: Passing (Green)
- ✅ CD Pipeline: Passing (Green)
- ✅ Application accessible at `http://<EC2-IP>:30001`

---

## 7. Limitations & Improvements

### Current Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Single-Node Cluster** | Cannot scale horizontally across machines | Sufficient for demo; migrate to EKS for production |
| **Raw Manifests** | Harder to manage configurations | Migrate to Helm Charts for templating |
| **No Monitoring** | Limited runtime visibility | Add Prometheus + Grafana stack |
| **Manual Scaling** | Replica count is static | Implement Horizontal Pod Autoscaler |
| **No Rollback Automation** | Failed deploys require manual intervention | Add automated rollback on health check failure |

### Proposed Improvements

1. **Helm Charts**: Package manifests for easier configuration management
2. **Monitoring Stack**: Prometheus for metrics, Grafana for visualization
3. **DAST Integration**: Add OWASP ZAP for dynamic security testing in CD
4. **GitOps**: Implement ArgoCD for declarative deployments
5. **Multi-Environment**: Add staging environment before production

---

## 8. Conclusion

This project successfully demonstrates a **production-grade DevSecOps pipeline** for the ReserveX application. By implementing:

- **10-stage CI pipeline** with comprehensive security scanning
- **5-stage CD pipeline** with self-healing Kubernetes deployment
- **Shift-Left Security** with SAST, SCA, and container scanning
- **Infrastructure-as-Code** with Kubernetes manifests

We have achieved the core goal: **Only clean, secure, and verified code reaches production—automatically.**

The pipeline serves as a foundation that can be extended with additional tools (Helm, Prometheus, ArgoCD) as the project matures. The lessons learned here—automation, security integration, and infrastructure abstraction—are directly applicable to enterprise DevOps environments.

---

## Appendix A: How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/harshpanchal04/ReserveX.git
cd ReserveX

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 4. Run the application
streamlit run app.py
```

## Appendix B: Secrets Configuration

To run the CI/CD pipeline, configure the following secrets in GitHub:

| Secret Name | How to Obtain |
|-------------|---------------|
| `DOCKERHUB_USERNAME` | Your DockerHub username |
| `DOCKERHUB_TOKEN` | DockerHub → Account Settings → Security → New Access Token |
| `EC2_HOST` | AWS Console → EC2 → Instances → Public IPv4 address |
| `EC2_SSH_KEY` | Content of your `.pem` file (include `-----BEGIN RSA PRIVATE KEY-----`) |

---

*Submitted for Advanced DevOps Assessment - January 2026*
