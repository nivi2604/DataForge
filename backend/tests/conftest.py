import sys
import os
from pathlib import Path

# Set the test database URL before any application code is imported
# This ensures that Settings (pydantic) loads this instead of the .env value.
TEST_DB_URL = "postgresql://postgres:Nivedha%402604@localhost:5432/dataforge_test"
os.environ["DATABASE_URL"] = TEST_DB_URL

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from app.db.base import Base
from app.db.session import engine
from app.core.config import settings

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    url_str = str(engine.url)

    # Add a safety guard to abort test setup if the database URL points to dataforge
    # and not dataforge_test.
    if "dataforge" in url_str and "dataforge_test" not in url_str:
        pytest.exit(f"ABORT: Connected to production database! URL: {url_str}")

    # Create all tables in the test database
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture(autouse=True)
def clear_repositories() -> None:
    url_str = str(engine.url)

    # Extra safety guard on teardown
    if "dataforge" in url_str and "dataforge_test" not in url_str:
        raise RuntimeError(f"ABORT: Attempted to clear production database! URL: {url_str}")

    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
