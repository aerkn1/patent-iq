# Patent IQ Backend

The backend service for Patent IQ, providing the REST API, data processing, and ML inference capabilities.

## Tech Stack

- **Framework**: FastAPI
- **Database**: DuckDB (OLAP), PostgreSQL (via PATSTAT)
- **Language**: Python 3.12+
- **Dependency Management**: Poetry
- **ML**: LightGBM, SHAP, Polars

## Prerequisites

- Python 3.12 or higher
- [Poetry](https://python-poetry.org/docs/#installation)

## Setup

1.  **Install dependencies**:
    ```bash
    poetry install
    ```

2.  **Environment Configuration**:
    Create a `.env` file in the `backend` directory.
    ```bash
    # Example .env configuration
    # Add required variables here
    ```

3.  **Run the Server**:
    Start the development server with hot-reloading:
    ```bash
    poetry run uvicorn main:app --reload --port 8000
    ```
    
    Or activate the virtual environment manually:
    ```bash
    source .venv/bin/activate
    uvicorn main:app --reload --port 8000
    ```

4.  **API Documentation**:
    Once running, visit:
    - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
    - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
