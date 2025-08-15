import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))
import universal_setup

import pytest
from datetime import datetime, timezone
from app.utils.datetime_utils import (
    get_utc_now, 
    format_datetime_for_api, 
    ensure_utc, 
    parse_datetime_from_api
)

@pytest.mark.unit
class TestDateTimeUtils:
    """Test per utilities datetime"""
    
    def test_get_utc_now(self):
        """Test che get_utc_now restituisca UTC"""
        now = get_utc_now()
        assert now.tzinfo == timezone.utc
        assert isinstance(now, datetime)
    
    def test_format_datetime_for_api(self):
        """Test formatazione datetime per API"""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        formatted = format_datetime_for_api(dt)
        assert formatted == "2024-01-15T10:30:00Z"
        
        # Test con None
        assert format_datetime_for_api(None) is None
    
    def test_ensure_utc(self):
        """Test conversione a UTC"""
        naive_dt = datetime(2024, 1, 15, 10, 30, 0)
        utc_dt = ensure_utc(naive_dt)
        assert utc_dt.tzinfo == timezone.utc
    
    def test_parse_datetime_from_api(self):
        """Test parsing da string ISO"""
        iso_string = "2024-01-15T10:30:00Z"
        parsed = parse_datetime_from_api(iso_string)
        assert isinstance(parsed, datetime)
        assert parsed.tzinfo is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
