"""
Tests for the task models in nexios_contrib.tasks.models.
"""
import asyncio
import time
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nexios_contrib.tasks.models import Task, TaskResult, TaskError
from nexios_contrib.tasks.config import TaskStatus

@pytest.fixture
async def sample_task():
    """Create a sample task for testing."""
    async def task_func(x, y):
        return x + y
    
    return Task(task_func, 2, 3, name="test_task")

@pytest.mark.asyncio
async def test_task_initialization():
    """Test task initialization with different parameters."""
    async def task_func():
        return "result"
    
    # Test with minimal parameters
    task = Task(task_func)
    assert task.name.startswith("task-")
    assert task.status == TaskStatus.PENDING
    assert task.args == ()
    assert task.kwargs == {}
    
    # Test with all parameters
    task = Task(task_func, 1, 2, 3, name="test", x=10, y=20)
    assert task.name == "test"
    assert task.args == (1, 2, 3)
    assert task.kwargs == {"x": 10, "y": 20}

@pytest.mark.asyncio
async def test_task_run(sample_task):
    """Test running a task and getting its result."""
    assert sample_task.status == TaskStatus.PENDING
    
    # Run the task
    await sample_task.run()
    
    # Verify the task completed successfully
    assert sample_task.status == TaskStatus.COMPLETED
    assert sample_task.result is not None
    assert sample_task.result.status == TaskStatus.COMPLETED
    assert sample_task.result.result == 5  # 2 + 3 = 5
    assert sample_task.result.error is None

@pytest.mark.asyncio
async def test_task_wait(sample_task):
    """Test waiting for a task to complete."""
    # Start the task in the background
    asyncio.create_task(sample_task.run())
    
    # Wait for the task to complete
    result = await sample_task.wait(timeout=1.0)
    
    # Verify the result
    assert result == 5  # 2 + 3 = 5
    assert sample_task.status == TaskStatus.COMPLETED

@pytest.mark.asyncio
async def test_task_error_handling():
    """Test error handling in tasks."""
    async def failing_task():
        raise ValueError("Test error")
    
    task = Task(failing_task, name="failing_task")
    
    # Run the task and expect an exception
    with pytest.raises(ValueError, match="Test error"):
        await task.run()
    
    # Verify the task failed with the correct error
    assert task.status == TaskStatus.FAILED
    assert task.result is not None
    assert task.result.status == TaskStatus.FAILED
    assert isinstance(task.result.error, ValueError)
    assert "Test error" in str(task.result.error)



@pytest.mark.asyncio
async def test_task_timeout():
    """Test task timeout handling."""
    async def long_running_task():
        await asyncio.sleep(10)
        return "too late"
    
    task = Task(long_running_task, name="timeout_test")
    
    # Wait for the task with a short timeout
    with pytest.raises(asyncio.TimeoutError):
        await task.wait(timeout=0.1)
    
    
    
    

def test_task_result_serialization():
    """Test serialization of task results."""
    # Test successful result
    result = TaskResult(
        task_id="123",
        result={"key": "value"},
        status=TaskStatus.COMPLETED,
        error=None,
        created_at=1000.0,
        completed_at=1001.5
    )
    
    result_dict = result.to_dict()
    assert result_dict == {
        "task_id": "123",
        "status": "COMPLETED",
        "result": "{'key': 'value'}",
        "error": None,
        "created_at": 1000.0,
        "completed_at": 1001.5,
        "duration": 1.5
    }
    
    # Test error result
    try:
        raise ValueError("Test error")
    except ValueError as e:
        error = e
    
    error_result = TaskResult(
        task_id="456",
        result=None,
        status=TaskStatus.FAILED,
        error=error,
        created_at=2000.0,
        completed_at=2000.5
    )
    
    error_dict = error_result.to_dict()
    assert error_dict["task_id"] == "456"
    assert error_dict["status"] == "FAILED"
    assert error_dict["result"] is None
    assert "Test error" in error_dict["error"]
    assert error_dict["created_at"] == 2000.0
    assert error_dict["completed_at"] == 2000.5
    assert error_dict["duration"] == 0.5
