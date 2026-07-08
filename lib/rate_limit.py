import time
import requests
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class GitHubRateLimiter:
    def __init__(self, calls_per_minute: int = 10, max_retries: int = 3):
        self.calls_per_minute = calls_per_minute
        self.max_retries = max_retries
        self.call_timestamps = []
        self.rate_limit_remaining = None
        self.rate_limit_reset = None

    def _proactive_throttle(self):
        now = time.time()
        
        if self.calls_per_minute > 0:
            min_interval = 60.0 / self.calls_per_minute
            if self.call_timestamps:
                time_since_last = now - self.call_timestamps[-1]
                if time_since_last < min_interval:
                    sleep_time = min_interval - time_since_last
                    logger.info(f"Proactive throttle: sleeping for {sleep_time:.2f} seconds to space requests")
                    time.sleep(sleep_time)
                    now = time.time()

        # Keep timestamps from the last 60 seconds
        self.call_timestamps = [t for t in self.call_timestamps if now - t < 60]
        
        if self.calls_per_minute > 0 and len(self.call_timestamps) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.call_timestamps[0])
            if sleep_time > 0:
                logger.info(f"Proactive throttle: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                now = time.time()
        
        self.call_timestamps.append(now)

    def update_from_headers(self, headers: dict):
        if "X-RateLimit-Remaining" in headers:
            self.rate_limit_remaining = int(headers["X-RateLimit-Remaining"])
        if "X-RateLimit-Reset" in headers:
            self.rate_limit_reset = int(headers["X-RateLimit-Reset"])

    def wait_if_needed(self):
        # Handle X-RateLimit-Remaining
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
            if self.rate_limit_reset is not None:
                sleep_time = self.rate_limit_reset - time.time()
                if sleep_time > 0:
                    logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds until reset.")
                    time.sleep(sleep_time)
            
            # Reset the values after sleeping
            self.rate_limit_remaining = None
            self.rate_limit_reset = None
            
        # Handle proactive throttling
        self._proactive_throttle()

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        retries = 0
        backoff = 1
        
        while True:
            self.wait_if_needed()
            
            try:
                result = func(*args, **kwargs)
                
                if isinstance(result, requests.Response):
                    self.update_from_headers(result.headers)
                    result.raise_for_status()
                    
                return result
                
            except requests.exceptions.RequestException as e:
                response = getattr(e, "response", None)
                
                # Check for secondary rate limit (403) or 429
                if response is not None and response.status_code in (403, 429):
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        sleep_time = int(retry_after)
                        logger.warning(f"Secondary rate limit hit. Sleeping for {sleep_time} seconds (Retry-After header).")
                        time.sleep(sleep_time)
                        # We don't increment retries for rate limits
                        continue
                        
                # Retry on network errors or 5xx server errors
                is_server_error = response is not None and 500 <= response.status_code < 600
                is_network_error = response is None # ConnectionError, Timeout, etc.
                
                if (is_network_error or is_server_error) and retries < self.max_retries:
                    logger.warning(f"Request failed ({type(e).__name__}). Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    retries += 1
                    backoff *= 2
                else:
                    # Reraise if we hit max retries or if it's a different error
                    
                    # For tests, we want to return the mock_response_500 if the exception is HTTPError
                    # but typically HTTPError is raised, let's just raise
                    # Wait, my test expects `result == mock_response_200`, meaning it returned the response,
                    # but if the func returned a response and we called raise_for_status() which raised,
                    # then we catch it, sleep, and try again, and next time it works.
                    raise e
