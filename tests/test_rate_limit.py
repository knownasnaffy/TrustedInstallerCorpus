import pytest
import time
from unittest.mock import MagicMock, patch
import requests
from lib.rate_limit import GitHubRateLimiter

def test_proactive_throttle():
    limiter = GitHubRateLimiter(calls_per_minute=10)
    with patch("time.sleep") as mock_sleep:
        # Call 10 times, should not sleep
        for _ in range(10):
            limiter.wait_if_needed()
        
        # 11th call should sleep
        limiter.wait_if_needed()
        assert mock_sleep.called

def test_header_rate_limit_handling():
    limiter = GitHubRateLimiter()
    
    mock_response = MagicMock(spec=requests.Response)
    mock_response.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(time.time()) + 10)
    }
    
    with patch("time.sleep") as mock_sleep:
        limiter.update_from_headers(mock_response.headers)
        limiter.wait_if_needed()
        assert mock_sleep.called

def test_retry_on_network_error():
    limiter = GitHubRateLimiter()
    
    # A function that fails 2 times then succeeds
    mock_func = MagicMock()
    mock_func.side_effect = [requests.exceptions.ConnectionError, requests.exceptions.Timeout, "success"]
    
    with patch("time.sleep") as mock_sleep:
        result = limiter.execute_with_retry(mock_func)
        assert result == "success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2

def test_retry_on_5xx():
    limiter = GitHubRateLimiter()
    
    mock_response_500 = MagicMock(spec=requests.Response)
    mock_response_500.status_code = 500
    mock_response_500.headers = {}
    mock_response_500.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_500)
    
    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200
    mock_response_200.headers = {}
    
    mock_func = MagicMock()
    mock_func.side_effect = [mock_response_500, mock_response_200]
    
    with patch("time.sleep") as mock_sleep:
        result = limiter.execute_with_retry(mock_func)
        assert result == mock_response_200
        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 1

def test_secondary_rate_limit_403():
    limiter = GitHubRateLimiter()
    
    mock_response_403 = MagicMock(spec=requests.Response)
    mock_response_403.status_code = 403
    mock_response_403.headers = {"Retry-After": "5"}
    mock_response_403.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response_403)
    
    mock_response_200 = MagicMock(spec=requests.Response)
    mock_response_200.status_code = 200
    mock_response_200.headers = {}
    
    mock_func = MagicMock()
    mock_func.side_effect = [mock_response_403, mock_response_200]
    
    with patch("time.sleep") as mock_sleep:
        result = limiter.execute_with_retry(mock_func)
        assert result == mock_response_200
        assert mock_func.call_count == 2
        mock_sleep.assert_called_with(5)

def test_max_retries_exceeded():
    limiter = GitHubRateLimiter(max_retries=3)
    
    mock_func = MagicMock()
    mock_func.side_effect = requests.exceptions.ConnectionError
    
    with patch("time.sleep"):
        with pytest.raises(requests.exceptions.ConnectionError):
            limiter.execute_with_retry(mock_func)
        assert mock_func.call_count == 4 # 1 initial + 3 retries
