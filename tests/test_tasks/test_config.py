"""
Tests for the task configuration in nexios_contrib.tasks.config.
"""
import logging
import pytest

from nexios_contrib.tasks.config import TaskConfig, TaskStatus, DEFAULT_CONFIG

def test_task_status_enum():
    """Test the TaskStatus enum values."""
    assert TaskStatus.PENDING == "PENDING"
    assert TaskStatus.RUNNING == "RUNNING"
    assert TaskStatus.COMPLETED == "COMPLETED"
    assert TaskStatus.FAILED == "FAILED"
    assert TaskStatus.CANCELLED == "CANCELLED"

def test_task_config_defaults():
    """Test TaskConfig default values."""
    config = TaskConfig()
    
    assert config.max_concurrent_tasks == 100
    assert config.default_timeout is None
    assert config.task_result_ttl == 3600  # 1 hour
    assert config.enable_task_history is True
    assert config.log_level == logging.INFO

def test_task_config_custom_values():
    """Test TaskConfig with custom values."""
    config = TaskConfig(
        max_concurrent_tasks=50,
        default_timeout=30.0,
        task_result_ttl=1800,  # 30 minutes
        enable_task_history=False,
        log_level=logging.DEBUG
    )
    
    assert config.max_concurrent_tasks == 50
    assert config.default_timeout == 30.0
    assert config.task_result_ttl == 1800
    assert config.enable_task_history is False
    assert config.log_level == logging.DEBUG

def test_task_config_to_dict():
    """Test converting TaskConfig to dictionary."""
    config = TaskConfig(
        max_concurrent_tasks=10,
        default_timeout=60.0,
        task_result_ttl=7200,
        enable_task_history=True,
        log_level=logging.WARNING
    )
    
    config_dict = config.to_dict()
    
    assert config_dict == {
        "max_concurrent_tasks": 10,
        "default_timeout": 60.0,
        "task_result_ttl": 7200,
        "enable_task_history": True,
        "log_level": logging.WARNING,
    }

def test_default_config():
    """Test the default configuration constant."""
    assert isinstance(DEFAULT_CONFIG, TaskConfig)
    assert DEFAULT_CONFIG.max_concurrent_tasks == 100
    assert DEFAULT_CONFIG.default_timeout is None
    assert DEFAULT_CONFIG.task_result_ttl == 3600
    assert DEFAULT_CONFIG.enable_task_history is True
    assert DEFAULT_CONFIG.log_level == logging.INFO

