"""Built-in task functions."""

import time
import subprocess
from typing import Any, Dict

import requests

from ..logging import get_logger

logger = get_logger(__name__)


def echo(message: str = "Hello World") -> str:
    """Simple echo task."""
    logger.info(f"Echo task: {message}")
    return f"Echo: {message}"


def sleep(seconds: int = 5) -> str:
    """Sleep task for testing."""
    logger.info(f"Sleeping for {seconds} seconds")
    time.sleep(seconds)
    return f"Slept for {seconds} seconds"


def http_call(url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """Make HTTP request."""
    logger.info(f"Making {method} request to {url}")
    
    response = requests.request(method, url, **kwargs)
    
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "text": response.text,
        "url": response.url
    }


def shell(command: str, **kwargs) -> Dict[str, Any]:
    """Execute shell command."""
    logger.info(f"Executing command: {command}")
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        **kwargs
    )
    
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr
    }
