import pytest
from datetime import datetime, timezone, timedelta
from app.services.scheduler_service import SchedulerService
from fastapi import HTTPException

def test_calculate_next_run_cron():
    svc = SchedulerService()
    base = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    # 1. Hourly (custom token)
    res = svc._calculate_next_run("hourly", base)
    assert res == datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc).isoformat()
    
    # 2. Daily (custom token)
    res = svc._calculate_next_run("daily", base)
    assert res == datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc).isoformat()
    
    # 3. Every 15 mins
    res = svc._calculate_next_run("*/15 * * * *", base)
    assert res == datetime(2023, 1, 1, 12, 15, 0, tzinfo=timezone.utc).isoformat()
    
    # 4. Hourly cron
    res = svc._calculate_next_run("0 * * * *", base)
    assert res == datetime(2023, 1, 1, 13, 0, 0, tzinfo=timezone.utc).isoformat()
    
    # 5. Every day at 8 AM
    res = svc._calculate_next_run("0 8 * * *", base)
    assert res == datetime(2023, 1, 2, 8, 0, 0, tzinfo=timezone.utc).isoformat()
    
    # 6. Invalid cron
    with pytest.raises(ValueError, match="Invalid cron expression"):
        svc._calculate_next_run("invalid * *", base)
