"""
Tests for the TaskManager class in nexios_contrib.tasks.manager.
"""
import asyncio
from pickle import FALSE
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nexios import NexiosApp
from nexios_contrib.tasks.manager import TaskManager
from nexios_contrib.tasks.models import Task, TaskResult, TaskError
from nexios_contrib.tasks.config import TaskStatus, TaskConfig

@pytest.fixture
def app():
    """Create a test Nexios app."""
    return NexiosApp()

@pytest.fixture
def task_manager(app):
    """Create a task manager instance for testing."""
    return TaskManager(app)

@pytest.fixture
async def async_task_manager(task_manager):
    """Create and start a task manager for async tests."""
    await task_manager.start()
    try:
        yield task_manager
    finally:
        await task_manager.shutdown()

@pytest.mark.asyncio
async def test_task_creation(task_manager):
    """Test creating a new task."""
    async def sample_task(x, y):
        return x + y
    
    task = await task_manager.create_task(sample_task, 2, 3)
    
    assert task is not None
    assert task.status == TaskStatus.PENDING
    assert len(task_manager.tasks) == 1
    assert task_manager.tasks[task.id] == task

@pytest.mark.asyncio
async def test_task_execution(async_task_manager):
    """Test task execution and result retrieval."""
    async def sample_task(x, y):
        return x * y
    
    task = await async_task_manager.create_task(sample_task, 4, 5)
    result = await task.wait()
    
    assert result == 20
    assert task.status == TaskStatus.COMPLETED
    assert task.result is not None
    assert task.result.status == TaskStatus.COMPLETED
    assert task.result.result == 20

@pytest.mark.asyncio
async def test_task_error_handling(async_task_manager):
    """Test error handling in tasks."""
    async def failing_task():
        raise ValueError("Something went wrong")
    
    task = await async_task_manager.create_task(failing_task)
    
    with pytest.raises(ValueError):
        await task.wait()
    
    assert task.status == TaskStatus.FAILED
    assert task.result is not None
    assert task.result.status == TaskStatus.FAILED
    assert "Something went wrong" in str(task.result.error)

@pytest.mark.asyncio
async def test_task_cancellation(async_task_manager):
    """Test task cancellation."""
    async def long_running_task():
        try:
            await asyncio.sleep(10)
            return "completed"
        except asyncio.CancelledError:
            return "cancelled"
    
    task = await async_task_manager.create_task(long_running_task)
    await asyncio.sleep(0.1)  # Let the task start
    
    canceled = await async_task_manager.cancel_task(task.id)
    assert canceled is True
    
    result = await task.wait()
    assert result == "cancelled"

@pytest.mark.asyncio
async def test_task_callbacks(async_task_manager):
    """Test task completion callbacks."""
    called = False    
    async def sample_task():
        return "success"
    async def callback(task_id, result, error):
        nonlocal called
        called = True
    
    task = await async_task_manager.create_task(sample_task)
    async_task_manager.add_callback(task, callback)
    
    await task.wait()
    
    assert called
   

@pytest.mark.asyncio
async def test_task_manager_shutdown(async_task_manager):
    """Test task manager shutdown behavior."""
    task_completed = asyncio.Event()
    
    async def long_running_task():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            task_completed.set()
            raise
    
    task = await async_task_manager.create_task(long_running_task)
    await asyncio.sleep(0.1)  # Let the task start
    
    # Shutdown should cancel running tasks
    await async_task_manager.shutdown()
    
    # Wait for the task to be cancelled
    await asyncio.wait_for(task_completed.wait(), timeout=1.0)
    assert task.status == TaskStatus.CANCELLED
