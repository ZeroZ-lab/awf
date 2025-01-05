import os
import sys
import pytest

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Configure pytest-asyncio
pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop_policy():
    """Configure the event loop policy for tests."""
    import asyncio
    return asyncio.get_event_loop_policy() 