# Expense Manager Backend (expenseManager_BE)

> A robust, containerized Django REST API designed for secure personal expense tracking and financial data management.

**Developer:** Girdhar Kumawat  
**Institution:** JECRC Foundation  
**Status:** Active  

## 2. Overview
**What the project does:** `expenseManager_BE` serves as the core backend infrastructure for an expense management ecosystem. It handles secure data persistence, business logic, and API routing.

**Problem it solves:** Provides a centralized, secure system to log, categorize, and retrieve financial transactions, replacing manual entry with a programmatic, easily integrated API backend.

**Main capabilities:**
* Secure user authentication and isolated data sessions.
* Granular expense tracking via structured CRUD operations.
* Consistent, reproducible environments utilizing Docker containerization.

## 3. Features
* **Modular Architecture:** Clean separation of concerns between user management (`account` app) and core business logic (`base` app).
* **RESTful API:** Structured JSON endpoints built with Django REST Framework.
* **Containerized Deployment:** Streamlined setup and production deployment using Docker.
* **Database Agnostic:** Configured for local development with SQLite, easily adaptable to robust relational databases like PostgreSQL.

## 4. Technology Stack

| Category | Technology | Language | Framework | Deployment |
| :--- | :--- | :--- | :--- | :--- |
| **Backend** | Python 3 | Python | Django / DRF | Docker |
| **Database** | SQLite (Dev) / PostgreSQL | SQL | Django ORM | Amazon Web Services (AWS EC2) |

## 5. Repository Structure
```text
expenseManager_BE/
├── account/               # App module: User profiles, authentication, and authorization
├── base/                  # App module: Core logic, models, and views for transactions
├── expenseManager_BE/     # Project root: Core configuration, settings.py, and URL routing
├── .dockerignore          # Specifies untracked files during Docker image build
├── .gitignore             # Specifies untracked files for Git
├── Dockerfile             # Environment instructions to build the application container
├── manage.py              # Django's administrative and execution utility
└── requirements.txt       # Python dependency manifest
