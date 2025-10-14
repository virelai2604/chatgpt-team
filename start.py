from helper import BASE_URL  # Add this line at the top

import pytest
import pytest_asyncio
import httpx
import asyncio

@pytest_asyncio.fixture(scope="session")
async def async_client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=180) as client:
        yield client
