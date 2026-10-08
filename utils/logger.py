"""
Comprehensive Logging Module - Production Ready
Centralized logging configuration for AC Service Billing Software
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output (does NOT mutate record)"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        formatted = super().format(record)
        return f"{log_color}{formatted}{self.COLORS['RESET']}"


def setup_logging(app_name="AC_Service_Billing", log_dir="logs", level=logging.INFO):
    """
    Setup comprehensive logging with file and console handlers
    
    Args:
        app_name: Application name for log files
        log_dir: Directory to store log files
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        dict: Logger instances for different components
    """
    project_root = Path(__file__).resolve().parent.parent
    if getattr(sys, 'frozen', False):
        app_data = Path(os.getenv('APPDATA', project_root)) / 'AnshAirCool'
        project_root = app_data
    resolved_log_dir = Path(log_dir)
    if not resolved_log_dir.is_absolute():
        resolved_log_dir = project_root / resolved_log_dir
    log_path = resolved_log_dir.resolve()
    log_path.mkdir(parents=True, exist_ok=True)

    loggers = [
        logging.getLogger(app_name),
        logging.getLogger(f"{app_name}.security"),
        logging.getLogger(f"{app_name}.database"),
        logging.getLogger(f"{app_name}.errors"),
    ]

    for logger in loggers:
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass

    # Main application logger
    logger = loggers[0]
    logger.setLevel(level)

    # Security logger (separate file for security events)
    security_logger = loggers[1]
    security_logger.setLevel(level)

    # Database logger
    db_logger = loggers[2]
    db_logger.setLevel(level)

    # Error logger (only errors and critical)
    error_logger = loggers[3]
    error_logger.setLevel(logging.ERROR)

    # Prevent log propagation to root logger
    for log in loggers:
        log.propagate = False
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    
    # Main log file handler with rotation
    main_log_file = log_path / f"{app_name}.log"
    file_handler = RotatingFileHandler(
        main_log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    
    # Security log file
    security_log_file = log_path / f"{app_name}_security.log"
    security_handler = RotatingFileHandler(
        security_log_file,
        maxBytes=10*1024*1024,
        backupCount=10,  # Keep more security logs
        encoding='utf-8'
    )
    security_handler.setLevel(level)
    security_handler.setFormatter(detailed_formatter)
    
    # Database log file
    db_log_file = log_path / f"{app_name}_database.log"
    db_handler = RotatingFileHandler(
        db_log_file,
        maxBytes=10*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    db_handler.setLevel(level)
    db_handler.setFormatter(detailed_formatter)
    
    # Error log file (all errors from all components)
    error_log_file = log_path / f"{app_name}_errors.log"
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10*1024*1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # Add handlers to loggers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    
    security_logger.addHandler(security_handler)
    security_logger.addHandler(error_handler)
    
    db_logger.addHandler(db_handler)
    db_logger.addHandler(error_handler)
    
    # Log initialization
    logger.info("=" * 80)
    logger.info(f"{app_name} Logging Initialized")
    logger.info(f"Log Directory: {log_path}")
    logger.info(f"Log Level: {logging.getLevelName(level)}")
    logger.info("=" * 80)
    
    return {
        'app': logger,
        'security': security_logger,
        'database': db_logger,
        'error': error_logger
    }


_logger_cache = {}

def get_logger(name):
    """
    Get a logger instance with the given name (cached, no duplicate handlers)
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    if name in _logger_cache:
        return _logger_cache[name]
    loggers = setup_logging()
    child = loggers['app'].getChild(name)
    _logger_cache[name] = child
    return child


# Global loggers instance
_loggers = None
logger = get_logger('app')


def get_loggers():
    """Get global loggers instance"""
    global _loggers
    if _loggers is None:
        _loggers = setup_logging()
    return _loggers


# Convenience functions
def log_debug(message, logger_name='app'):
    """Log debug message"""
    loggers = get_loggers()
    loggers[logger_name].debug(message)


def log_info(message, logger_name='app'):
    """Log info message"""
    loggers = get_loggers()
    loggers[logger_name].info(message)


def log_warning(message, logger_name='app'):
    """Log warning message"""
    loggers = get_loggers()
    loggers[logger_name].warning(message)


def log_error(message, logger_name='app', exc_info=False):
    """Log error message with optional exception info"""
    loggers = get_loggers()
    loggers[logger_name].error(message, exc_info=exc_info)


def log_critical(message, logger_name='app', exc_info=True):
    """Log critical message with exception info"""
    loggers = get_loggers()
    loggers[logger_name].critical(message, exc_info=exc_info)


def log_security_event(event_type, details=None, username=None):
    """Log security-related event"""
    loggers = get_loggers()
    message = f"[{event_type}]"
    if username:
        message += f" User: {username}"
    if details:
        message += f" Details: {details}"
    loggers['security'].info(message)


def log_database_query(query, params=None, duration=None):
    """Log database query for debugging"""
    loggers = get_loggers()
    message = f"SQL: {query[:200]}"
    if params:
        message += f" Params: {params}"
    if duration:
        message += f" Duration: {duration:.3f}s"
    loggers['database'].debug(message)
