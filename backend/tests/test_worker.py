import asyncio
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.scheduler_worker import worker
from app.core.config import settings

@pytest.fixture
def override_polling_interval():
    original = settings.scheduler_polling_interval
    settings.scheduler_polling_interval = 0.1
    yield
    settings.scheduler_polling_interval = original

def test_scheduler_worker_lifecycle(override_polling_interval):
    assert worker.running is False
    assert worker.task is None
    
    with patch.object(worker.scheduler_service, 'trigger_due_schedules') as mock_trigger:
        with TestClient(app) as client:
            assert worker.running is True
            assert worker.task is not None
            
            # Allow time for polling loop to execute
            import time
            time.sleep(0.3)
            
            assert mock_trigger.called
            
        assert worker.running is False
        assert worker.task is None

def test_scheduler_worker_duplicate_prevention(override_polling_interval):
    with TestClient(app) as client:
        task1 = worker.task
        assert worker.running is True
        
        # Calling start again should not create a new task
        worker.start()
        assert worker.task is task1

def test_scheduler_worker_exception_handling(override_polling_interval):
    # Test that exception in the loop doesn't kill it
    with patch.object(worker.scheduler_service, 'trigger_due_schedules') as mock_trigger:
        mock_trigger.side_effect = [Exception("Test error"), None]
        
        with TestClient(app):
            import time
            time.sleep(0.3)
            
            # Should have called it multiple times despite the first exception
            assert mock_trigger.call_count >= 2
            assert worker.running is True
