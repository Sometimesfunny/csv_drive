import asyncio
import pytest
from src.database.models import Base


@pytest.fixture(scope='session', autouse=True)
def event_loop():
    """
    Creates an instance of the default event loop for the test session.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
    