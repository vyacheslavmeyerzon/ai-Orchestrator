# common/logger.py
"""
Logging configuration for AI Test Orchestrator
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""

        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields if present
        if hasattr(record, 'agent_type'):
            log_data['agent_type'] = record.agent_type

        if hasattr(record, 'project_id'):
            log_data['project_id'] = record.project_id

        if hasattr(record, 'operation'):
            log_data['operation'] = record.operation

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability"""

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output"""
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET

        # Format: [TIME] LEVEL [AGENT] MESSAGE
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        agent_info = f"[{getattr(record, 'agent_type', 'SYSTEM')}]"

        formatted_message = f"{color}[{time_str}] {record.levelname} {agent_info} {record.getMessage()}{reset}"

        return formatted_message


def setup_logging(log_level: str = "INFO", log_file: str = "./logs/orchestrator.log") -> logging.Logger:
    """Setup logging configuration for the orchestrator"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # Get root logger
    logger = logging.getLogger('orchestrator')
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with colored output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredConsoleFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with structured JSON logging
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_agent_logger(agent_type: str) -> logging.Logger:
    """Get logger for specific agent with context"""
    logger = logging.getLogger(f'orchestrator.{agent_type}')

    # Add agent type to all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.agent_type = agent_type.upper()
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


def log_operation(operation: str, project_id: str = None):
    """Decorator for logging operations"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('orchestrator')

            # Create log record with extra context
            extra = {
                'operation': operation,
                'project_id': project_id or 'unknown'
            }

            logger.info(f"Starting operation: {operation}", extra=extra)

            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed operation: {operation}", extra=extra)
                return result

            except Exception as e:
                logger.error(f"Failed operation: {operation} - {str(e)}", extra=extra)
                raise

        return wrapper

    return decorator


# Initialize default logger
def init_default_logger():
    """Initialize default logger with basic configuration"""
    return setup_logging()


# Test function
if __name__ == "__main__":
    # Test logging setup
    logger = setup_logging("DEBUG", "./logs/test.log")

    logger.info("Testing orchestrator logger")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test agent logger
    api_logger = get_agent_logger("api_agent")
    api_logger.info("Testing API agent logger")

    print("Logger test completed. Check logs directory.")