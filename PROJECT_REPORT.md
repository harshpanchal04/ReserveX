# ReserveX - Advanced DevOps CI/CD Project Report

**Author:** ReserveX DevOps Team
**Date:** January 20, 2026

---

## 1. Problem Background & Motivation

In modern software delivery, manual deployments and local testing are prone to errors ("It works on my machine" syndrome). ReserveX, a complex web scraping application, faces specific challenges:
-   **Dependency Risks**: Vulnerabilities in Python packages or the base Docker image.
-   **Regression Bugs**: Changes to the seat-finding algorithm breaking core functionality.
-   **Deployment Complexity**: Ensuring the application runs identically in production as it does locally.

The goal of this project is to implement a **Robust CI/CD Pipeline** that automates verification, security scanning, and deployment, ensuring that only "Clean, Secure, and Working" code reaches the production environment.

## 2. Application Overview

**ReserveX (Train Surfer)** is a Python-based web application built with **Streamlit**.
-   **Core Logic**: `solver.py` contains the "Hacker Chain" algorithm.
-   **Data Fetching**: `scraper.py` uses **Playwright** to interact with IRCTC APIs.
-   **Containerization**: Packaged as a Docker container based on the official Playwright image.

## 3. CI/CD Architecture

We implemented a Multi-Stage Pipeline using **GitHub Actions**.

```mermaid
graph LR
    User[Developer] -->|Push Code| GitHub
    subgraph CI_Pipeline
        GitHub --> Lint[Linting (Flake8)]
        GitHub --> Test[Unit Tests (Pytest)]
        GitHub --> SAST[CodeQL Analysis]
        GitHub --> SCA[OWASP Dep Check]
        Lint & Test & SAST & SCA --> Build[Docker Build]
        Build --> Smoke[Smoke Test (Curl)]
        Smoke --> ImgScan[Image Scan (Trivy)]
        ImgScan --> Push[Push to DockerHub]
    end
    
    subgraph CD_Pipeline
        Push --> Deploy[Deploy to EC2+K3s]
        Deploy --> DAST[E2E Smoke Test]
        DAST --> Output[Deployment Complete]
    end
```

## 4. Pipeline Design & Stages

### Continuous Integration (CI)
*File: `.github/workflows/ci.yml`*

| Stage | Tool | Purpose | Why it matters |
|-------|------|---------|----------------|
| **Setup** | `actions/setup-python` | Initializes runner & caches dependencies. | **Speed**: Caching pip packages prevents re-downloading libraries on every build. |
| **Linting** | `flake8` | Enforces PEP8 style. | Prevents technical debt and ensures code readability. |
| **SAST** | `CodeQL` | Advanced Static Analysis. | Detects deep logic errors and security flaws (GitHub native). |
| **SCA** | `OWASP DC` | Software Composition Analysis. | Checks `requirements.txt` against NVD CVEs to prevent supply-chain attacks. |
| **Unit Tests** | `pytest` | Functional testing. | Ensures the "Seat Hopping" logic is correct before building. |
| **Smoke Test** | `curl` | Build Verification. | Boots the container in CI to ensure it doesn't crash on startup (e.g., missing env vars). |
| **Img Scan** | `trivy` | Container Security. | Detects OS-level vulnerabilities in the base Docker image before pushing. |

### Continuous Deployment (CD)
*File: `.github/workflows/cd.yml`*

| Stage | Tool | Purpose | Why it matters |
|-------|------|---------|----------------|
| **Deploy** | `SCP + SSH` | Deployment to Production. | **Efficiency**: Copies manifests to **K3s (Lightweight K8s)** and applies them natively. Eliminates Docker-in-Docker overhead. |
| **E2E Health Check** | `Python Requests` | Verifies HTTP 200 OK & checks for UI elements. | **Black-box Testing**: Proves the app is actually serving traffic after deployment, not just that the container is running. |

## 5. Security & Quality Controls (DevSecOps)

We adopted a **Shift-Left Security** approach:
1.  **Code Level**: `CodeQL` runs deep semantic analysis on every commit.
2.  **Dependency Level**: `OWASP Dependency Check` scans libraries for known vulnerabilities.
3.  **Container Level**: `trivy` scans the final artifact for OS vulnerabilities.
4.  **Runtime Level**: `Smoke Tests` (in CI) and `DAST` (in CD) verify the application structure.

**Secrets Management**:
-   `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`: Scoped to DockerHub interaction.
-   `EC2_HOST`, `EC2_SSH_KEY`: securely stored in GitHub Secrets to allow the runner to authenticate with the deployment server without exposing credentials.

## 6. Kubernetes Implementation

To balance cost and realism, we utilized a **Simulated Production Environment**:
-   **Cluster Architecture**: We deployed a Single-Node **K3s Cluster** on an Amazon EC2 instance.
-   **Reasoning**: K3s is a certified lightweight Kubernetes distribution designed for production. Unlike Minikube (which uses nested virtualization), K3s runs natively on Linux processes, reducing RAM usage by ~50% and improving stability on small EC2 instances.
-   **Deployment**: We use standard `deployment.yaml` and `service.yaml` manifests.
-   **Zero-Downtime**: Kubernetes handles the rolling update of pods.

## 7. Results & Observations

-   **Reliability**: Logic bugs are caught by `test_solver.py` before they break the build.
-   **Security**: The workflow blocks builds if `OWASP` or `CodeQL` detect High-Severity issues.
-   **Realism**: Using SSH to deploy to a remote EC2 instance simulates a real-world "Push based" cd workflow.

## 8. Limitations & Future Improvements

-   **Scaling**: The current Single-Node Minikube setup cannot scale horizontally across machines. Migration to EKS would solve this.
-   **Helm**: We are using raw manifests. Migrating to **Helm Charts** would improve manageability.
-   **Monitoring**: Integration with Prometheus/Grafana for runtime metrics.

---
*Verified Implementation for Advanced DevOps Assessment.*
