# Task Management API

A production-grade **Task Management REST API** built with **FastAPI** and **PostgreSQL**, containerized with **Docker**, and deployed on **AWS ECS Fargate** via an automated **GitHub Actions CI/CD pipeline**.

---

##  Architecture Overview
```
                        ┌─────────────────────────────────────────┐
                        │              GitHub Actions              │
                        │  (CI/CD: lint → test → build → deploy)  │
                        └──────────────────┬──────────────────────┘
                                           │ push to main
                                           ▼
┌───────────┐     HTTPS      ┌─────────────────────┐
│  Client   │ ─────────────► │   AWS ECS Fargate    │
│ (Browser/ │                │  (Docker Container)  │
│   curl)   │ ◄───────────── │    FastAPI + Uvicorn │
└───────────┘                └──────────┬──────────┘
                                        │
                              ┌─────────▼──────────┐
                              │    AWS RDS          │
                              │  (PostgreSQL)       │
                              └────────────────────┘

             ┌─────────────────────────────────────┐
             │         AWS ECR                     │
             │  (Docker image registry)            │
             └─────────────────────────────────────┘
```

---

## Technology Stack

| Component       | Technology                        | Reason                                                     |
|----------------|-----------------------------------|------------------------------------------------------------|
| API Framework  | **FastAPI**                       | Async support, auto Swagger docs, high performance         |
| Database       | **PostgreSQL (AWS RDS)**          | Production-grade, managed, reliable relational storage     |
| ORM            | **SQLAlchemy (async)**            | Async ORM with full PostgreSQL support via `asyncpg`       |
| Containerization | **Docker**                      | Consistent, reproducible environments                      |
| Container Registry | **AWS ECR**                   | Native integration with ECS, secure image storage          |
| Cloud Hosting  | **AWS ECS Fargate**               | Serverless containers, no EC2 management needed            |
| CI/CD          | **GitHub Actions**                | Automated lint, test, build, and deploy on every push      |
| Testing        | **pytest + pytest-asyncio**       | Async-first test suite with isolated DB per test           |
| Linting        | **flake8**                        | Enforces code style and quality checks                     |

---

##  Design Choices

- **FastAPI over Flask**: FastAPI's async-native design pairs naturally with `asyncpg` and SQLAlchemy async sessions, making every database call non-blocking. Its built-in OpenAPI/Swagger documentation also satisfies the API docs requirement out of the box.

- **ECS Fargate over Lambda**: The API uses SQLAlchemy connection pooling and persistent async sessions. Lambda's cold-start and ephemeral nature makes connection management complex. Fargate gives full container control with auto-scaling and no server management.

- **AWS RDS PostgreSQL**: Managed service with automated backups, Multi-AZ support, and seamless connectivity to ECS via VPC security groups — no manual database provisioning needed.

- **NullPool in tests**: Tests use `NullPool` to avoid connection leaks between test cases — each test gets a fresh schema via `drop_all` / `create_all`.

---

##  Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, route definitions
│   ├── model.py         # SQLAlchemy ORM models
│   ├── schema.py        # Pydantic request/response schemas
│   └── database.py      # Async engine, session factory
├── tests/
│   └── test_api.py      # pytest async test suite
├── .github/
│   └── workflows/
│       └── deploy.yml   # GitHub Actions CI/CD pipeline
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

---

##  Running Locally

### Prerequisites
- Python 3.12+
- PostgreSQL running locally (or Docker)
- Docker (optional, for containerized run)

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/taskdb
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

##  Running with Docker

### Build the image

```bash
docker build -t task-api .
```

### Run the container

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@host.docker.internal:5432/taskdb \
  task-api
```

---

##  Running Tests

Tests use a separate test database session and reset the schema before each test.

```bash
# Make sure DATABASE_URL is set in your .env
pytest
```

Expected output:
```
collected 8 items

tests/test_api.py::test_root                    PASSED
tests/test_api.py::test_create_task             PASSED
tests/test_api.py::test_get_all_tasks           PASSED
tests/test_api.py::test_get_single_task         PASSED
tests/test_api.py::test_get_task_not_found      PASSED
tests/test_api.py::test_update_task_status      PASSED
tests/test_api.py::test_update_task_invalid_status PASSED
tests/test_api.py::test_delete_task             PASSED

8 passed in X.XXs
```

---

##  API Endpoints

Base URL: `http://<your-deployment-url>`

### `GET /`
Health check.

**Response:**
```json
"Task manager API is running"
```

---

### `POST /tasks`
Create a new task.

**Request Body:**
```json
{
  "title": "Complete internship assessment",
  "description": "Build and deploy the Task Management API"
}
```

**Response `201`:**
```json
{
  "id": 1,
  "title": "Complete internship assessment",
  "description": "Build and deploy the Task Management API",
  "status": "pending",
  "created_at": "2026-05-21T10:30:00Z",
  "updated_at": "2026-05-21T10:30:00Z"
}
```

---

### `GET /tasks`
List all tasks.

**Response `200`:**
```json
[
  {
    "id": 1,
    "title": "Complete internship assessment",
    "status": "pending",
    "created_at": "2026-05-21T10:30:00Z",
    "updated_at": "2026-05-21T10:30:00Z"
  }
]
```

---

### `GET /tasks/{id}`
Get a specific task by ID.

**Response `200`:**
```json
{
  "id": 1,
  "title": "Complete internship assessment",
  "status": "pending",
  "created_at": "2026-05-21T10:30:00Z",
  "updated_at": "2026-05-21T10:30:00Z"
}
```

**Response `404`:**
```json
{ "detail": "Task not found" }
```

---

### `PATCH /tasks/{id}/status`
Update a task's status.

**Request Body:**
```json
{ "status": "completed" }
```

**Response `200`:**
```json
{
  "id": 1,
  "title": "Complete internship assessment",
  "status": "completed",
  "updated_at": "2026-05-21T11:00:00Z"
}
```

**Response `422`** (invalid status):
```json
{ "detail": "Status must be 'pending' or 'completed'" }
```

---

### `DELETE /tasks/{id}`
Delete a task by ID.

**Response `200`:**
```json
{ "message": "Record id 1 deleted successfully" }
```

**Response `404`:**
```json
{ "detail": "Task not found" }
```

---

## CI/CD Pipeline (GitHub Actions)

The pipeline is defined in `.github/workflows/deploy.yml` and triggers on every push to `main`.

```
push to main
     │
     ▼
┌─────────────────────────┐
│  1. Checkout Code        │
├─────────────────────────┤
│  2. Set up Python 3.12   │
├─────────────────────────┤
│  3. Install dependencies │
├─────────────────────────┤
│  4. Run flake8 (lint)    │
├─────────────────────────┤
│  5. Run pytest (tests)   │
├─────────────────────────┤
│  6. Configure AWS creds  │
├─────────────────────────┤
│  7. Login to ECR         │
├─────────────────────────┤
│  8. Build & push image   │
│     (linux/arm64)        │
├─────────────────────────┤
│  9. Force ECS redeploy   │
└─────────────────────────┘
```

### Required GitHub Secrets & Variables

| Name                    | Type     | Description                            |
|------------------------|----------|----------------------------------------|
| `AWS_ACCESS_KEY_ID`    | Secret   | AWS IAM access key                     |
| `AWS_SECRET_ACCESS_KEY`| Secret   | AWS IAM secret key                     |
| `DATABASE_URL`         | Secret   | PostgreSQL connection string for tests |
| `AWS_REGION`           | Variable | e.g. `ap-south-2`                      |
| `ECR_REPOSITORY`       | Variable | ECR repo name                          |
| `ECS_CLUSTER`          | Variable | ECS cluster name                       |
| `ECS_SERVICE`          | Variable | ECS service name                       |

---

## AWS Deployment

### Services Used
- **Amazon ECR** — stores versioned Docker images (tagged with `latest` and `git SHA`)
- **Amazon ECS Fargate** — runs the containerized API without managing servers
- **AWS RDS (PostgreSQL)** — managed relational database in a private VPC subnet
- **IAM** — least-privilege roles for ECS task execution and ECR access

### Deployment Steps (manual first-time setup)

1. **Create ECR repository** and note the URI.
2. **Create RDS PostgreSQL instance** in a private subnet; note the connection string.
3. **Create ECS Cluster** (Fargate type).
4. **Create Task Definition** referencing the ECR image, setting `DATABASE_URL` as an environment variable (from Secrets Manager or directly).
5. **Create ECS Service** from the task definition.
6. Add GitHub repository secrets and variables as listed above.
7. Push to `main` — GitHub Actions handles all subsequent deployments automatically.

---

##  Security Notes

- `.env` is listed in `.gitignore` — never committed to version control.
- All secrets (AWS keys, database URL) are stored in GitHub Secrets, not in code.
- RDS instance is in a private subnet, accessible only from the ECS task security group.

