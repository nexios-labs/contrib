"""
Tests for the task dependencies in nexios_contrib.tasks.dependency.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nexios.http import Request
from nexios_contrib.tasks.dependency import TaskDepend, get_task_dependency, TaskDependency
from nexios_contrib.tasks.models import Task, TaskResult
from nexios_contrib.tasks.config import TaskStatus

@pytest.fixture
def mock_request():
    """Create a mock request with a task manager."""
    request = MagicMock(spec=Request)
    request.base_app.task_manager = MagicMock()
    return request

@pytest.fixture
def task_depend(mock_request):
    """Create a TaskDepend instance with a mock request."""
    return TaskDepend(mock_request)


@pytest.mark.asyncio
async def test_task_depend_get_task(task_depend, mock_request):
    """Test getting a task by ID."""
    # Setup
    mock_task = MagicMock()
    mock_request.base_app.task_manager.get_task.return_value = mock_task
    
    # Test
    task_id = "test-task-id"
    result = await task_depend.get_task(task_id)
    
    # Verify
    assert result == mock_task
    mock_request.base_app.task_manager.get_task.assert_called_once_with(task_id)

@pytest.mark.asyncio
async def test_task_depend_wait_for_task(task_depend, mock_request):
    """Test waiting for a task to complete."""
    # Setup
    expected_result = "task result"
    mock_request.base_app.task_manager.wait_for_task = AsyncMock(return_value=expected_result)
    
    # Test
    task_id = "test-task-id"
    result = await task_depend.wait_for_task(task_id, timeout=5.0)
    
    # Verify
    assert result == expected_result
    mock_request.base_app.task_manager.wait_for_task.assert_called_once_with(
        task_id,
        timeout=5.0
    )

@pytest.mark.asyncio
async def test_task_depend_cancel_task(task_depend, mock_request):
    """Test cancelling a task."""
    # Setup
    mock_request.base_app.task_manager.cancel_task = AsyncMock(return_value=True)
    
    # Test
    task_id = "test-task-id"
    result = await task_depend.cancel_task(task_id)
    
    # Verify
    assert result is True
    mock_request.base_app.task_manager.cancel_task.assert_called_once_with(task_id)



def test_task_dependency():
    """Test the TaskDependency function."""
    # Test
    result = TaskDependency()
    
    # Verify
    from nexios.dependencies import Depend
    assert isinstance(result, Depend)
    assert result.dependency == get_task_dependency

