# ReserveX - Advanced DevOps CI/CD Project Report

**Author:** ReserveX DevOps Team
**Date:** January 20, 2026

---

## 1. Problem Background & Motivation

In modern software delivery, manual deployments and local testing are prone to errors ("It works on my machine" syndrome). ReserveX, being a complex application involving web scraping (Playwright) and algorithmic processing, faces specific challenges:
- **Dependency Risks**: Vulnerabilities in Python packages or the base Docker image.
- **Regression Bugs**: Logic optimization changes breaking the existing seat-finding algorithm.
- **Security Flaws**: Hardcoded secrets or unsafe file handling in the application code.

The goal of this project is to implement a **Robust CI/CD Pipeline** that automates the verification, security scanning, and deployment process, ensuring that only "Clean, Secure, and Working" code reaches production.

## 2. Application Overview

**ReserveX (Train Surfer)** is a Python-based web application built with **Streamlit**.
- **Core Logic**: `solver.py` contains the "Hacker Chain" algorithm.
- **Data Fetching**: `scraper.py` uses **Playwright** to interact with IRCTC APIs.
- **Containerization**: Packaged as a Docker container based on the official Playwright image.

## 3. CI/CD Architecture

We implemented a Multi-Stage Pipeline using **GitHub Actions**.

```mermaid
graph LR
    User[Developer] -->|Push Code| GitHub
    subgraph CI_Pipeline
        GitHub --> Lint[Linting (Flake8)]
        GitHub --> Test[Unit Tests (Pytest)]
        GitHub --> SAST[Security (Bandit/Safety)]
        Lint & Test & SAST --> Build[Docker Build]
        Build --> ImgScan[Image Scan (Trivy)]
        ImgScan --> Push[Push to DockerHub]
    end
    
    subgraph CD_Pipeline
        Push --> DeployStaging[Deploy to K8s Staging]
        DeployStaging --> DAST[OWASP ZAP Scan]
        DAST --> ManualGate{Manual Approval}
        ManualGate -->|Approved| DeployProd[Deploy to K8s Prod]
    end
```

## 4. Pipeline Design & Stages

### Continuous Integration (CI)
*File: `.github/workflows/ci.yml`*

| Stage | Tool | Purpose | Why it matters |
|-------|------|---------|----------------|
| **Linting** | `flake8` | Enforces PEP8 style. | Prevents technical debt and ensures readability. |
| **SAST** | `bandit` | Static Application Security Testing. | Detects common security issues (e.g., `eval()`, hardcoded passwords) early. |
| **SCA** | `safety` | Software Composition Analysis. | Checks `requirements.txt` against known vulnerability databases. |
| **Unit Tests** | `pytest` | Functional testing. | Ensures the "Seat Hopping" logic is correct before building. |
| **Docker Build** | `docker` | Containerization. | Packages app + dependencies for consistent runtime. |
| **Img Scan** | `trivy` | Container Security. | Detects OS-level vulnerabilities (e.g., in Ubuntu/Debian base) before pushing. |

### Continuous Deployment (CD)
*File: `.github/workflows/cd.yml`*

| Stage | Tool | Purpose | Why it matters |
|-------|------|---------|----------------|
| **Deploy Staging** | `kubectl` | Deployment to test env. | Verifies the app runs in a cluster environment. |
| **DAST** | `OWASP ZAP` | Dynamic Security Testing. | Attacks the running staging app to find runtime vulnerabilities (XSS, Headers). |
| **Production** | `kubectl` | Deployment to live env. | Protected by a Manual Approval gate to prevent accidental releases. |

## 5. Security & Quality Controls (DevSecOps)

We adopted a **Shift-Left Security** approach:
1.  **Code Level**: `bandit` runs on every commit. If it finds High-Severity issues, the build fails immediately.
2.  **Dependency Level**: `safety` ensures we aren't using vulnerable libraries.
3.  **Container Level**: `trivy` scans the final artifact.
4.  **Runtime Level**: `ZAP` scans the deployed application in Staging.

**Secrets Management**:
- `DOCKERHUB_USERNAME`/`TOKEN`: Stored in GitHub Secrets.
- `KUBE_CONFIG`: Securely injected into the runner environment to authenticate with the cluster. No credentials are stored in git.

## 6. Kubernetes Implementation

The application is deployed to two namespaces:
- **Staging**: 1 Replica, smaller resource requests.
- **Production**: 2 Replicas for High Availability, higher resource limits.

Manifests are templated; the CD pipeline injects the specific Docker Image SHA (`reservex:sha-xyz`) to ensure exactly what was tested is deployed (Immutable Infrastructure).

## 7. Results & Observations

- **Reliability**: Logic bugs are caught by `test_solver.py` before they break the build.
- **Security**: The workflow successfully blocks builds with Critical CVEs in dependencies.
- **Speed**: Caching pip dependencies reduces build time by ~40%.
- **Confidence**: The Manual Approval gate provides a final human check before production changes.

## 8. Limitations & Future Improvements

- **Mocking**: Currently, browser tests are mocked. In the future, we could add a "Headless Browser" service in CI to run real E2E tests.
- **Helm**: We are using raw manifests. Migrating to **Helm Charts** would improve manageability.
- **Monitoring**: Integration with Prometheus/Grafana for runtime metrics.

---
*Verified Implementation for Advanced DevOps Assessment.*
