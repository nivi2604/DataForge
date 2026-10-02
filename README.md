# DataForge

DataForge is a visual data engineering and pipeline orchestration platform. It is designed to orchestrate complex data workflows visually while providing powerful backend transformation, quality assurance, and automated integration with version control systems like GitHub.

## Problem
Building and maintaining data pipelines typically requires writing dense scripts, managing complex deployment strategies, and manually verifying data quality and schemas. This creates friction between data engineers, analysts, and software engineers, reducing agility and increasing the risk of data errors slipping into production.

## Solution
DataForge provides a unified platform where users can visually construct data pipelines as Directed Acyclic Graphs (DAGs). It simplifies the entire data journey—from extraction to transformation, data quality validation, and loading—while ensuring production-ready reliability through automated GitHub Pull Request workflows, scheduling, and pipeline versioning.

## Architecture
DataForge uses a robust, scalable architecture:
- **Frontend**: A dynamic, responsive React + TypeScript interface using React Flow for the visual pipeline builder.
- **Backend**: A high-performance FastAPI server managing execution logic, state, and external integrations.
- **Persistence**: PostgreSQL database managed via SQLAlchemy ORM for robust transactional integrity.
- **Execution Engine**: A deterministic pipeline executor that safely handles dependencies, retries, and failure propagation.

## Tech Stack
- **Frontend**: React 18, TypeScript, Vite, React Flow, Axios, Lucide React
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy 2.0, Pydantic, Uvicorn
- **Database**: PostgreSQL (Production) / SQLite-compatible
- **Security**: JWT-based Authentication, Bcrypt password hashing, Fernet encryption for secrets

## Pipeline Workflow
DataForge orchestrates data through discrete pipeline nodes:
1. **Extract**: Ingest data from external sources like PostgreSQL databases, CSV, JSON, Parquet, or GitHub repositories.
2. **Transform**: Apply structural, relational, and aggregation operations.
3. **Data Quality**: Evaluate datasets against rigorous validation rules.
4. **Load**: Safely export the processed data back to target systems or trigger automated PRs on GitHub.

## Transformations
The execution engine supports high-value data engineering transformations, executed reliably:
- **Row Operations**: Filter datasets based on conditions.
- **Column Operations**: Select, rename, and drop columns.
- **Type Operations**: Safely cast column types (Integer, Float, Boolean, String).
- **Relational Operations**: Perform Inner, Left, and Right joins to merge datasets.
- **Aggregations**: Group by columns and compute metrics (Count, Sum, Average, Min, Max).

## Data Quality
Ensure trustworthy outputs before they reach downstream systems. The Data Quality Engine deterministically evaluates:
- Missing values and duplicate rows.
- Schema conformity (Required columns).
- Type validation (Expected data types per column).
- Uniqueness validation (Ensuring critical columns contain unique values).
- Email format validation.

## SQL / PostgreSQL Engine
SQL is leveraged as a core capability for data engineering:
- **Query Builder**: Construct parameterized SQL queries (SELECT, JOIN, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT) directly from the visual interface.
- **Safety**: Uses parameterized queries via SQLAlchemy to prevent SQL injection.
- **Integrity**: Transactional execution and connection management ensure reliable data reads and writes.

## GitHub Integration & PR Validation
DataForge natively supports GitOps workflows:
- Extract input files directly from GitHub branches.
- Export processed outputs automatically by creating new branches and Pull Requests.
- Receive GitHub webhooks to validate pipeline status directly inside DataForge.
- Maintain continuous integration for data assets without exposing credentials.

## Versioning and Rollback
Pipelines evolve. DataForge tracks changes by saving version snapshots. Users can compare configurations across versions and instantly rollback to a previous known-good state if a pipeline fails.

## Scheduling
Pipelines can run manually or on an automated schedule (Hourly, Daily, Weekly, or custom cron expressions). The integrated scheduler worker runs alongside the API, allowing seamless unattended data operations.

## Security
- **Authentication**: JWT-based secure login.
- **Authorization**: Strict cross-tenant isolation ensures users can only access resources within their own organization.
- **Credentials**: Passwords are securely hashed (bcrypt). External credentials (like GitHub secrets) are encrypted at rest using Fernet.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL (or local SQLite database for development)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Configure your environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

Start the backend API server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```
The API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
```

Configure the frontend environment:
```bash
cp .env.example .env
```

Start the development server:
```bash
npm run dev
```
Open `http://localhost:5173` in your browser.

## Running Tests

### Backend Tests
Execute the full pytest suite (194 tests covering API, auth, transformations, scheduling, data quality, and GitHub integration):
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Build & Type Check
Verify TypeScript types and build the production bundle:
```bash
cd frontend
npm run build
```

## Known Limitations
- The Pipeline Transform layer officially supports CSV, JSON, Parquet, and PostgreSQL operations. Kafka remains unmapped.
- Scheduler worker runs as an in-process async worker; distributed multi-node workers require an external queue (Celery/Temporal).
