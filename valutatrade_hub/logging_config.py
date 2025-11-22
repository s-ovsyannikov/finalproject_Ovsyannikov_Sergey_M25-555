import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    """настройка логирования"""
 
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    

    formatter = logging.Formatter(
        fmt='%(levelname)s %(asctime)s %(name)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "actions.log",
        maxBytes=10*1024*1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    action_logger = logging.getLogger('actions')
    action_logger.setLevel(logging.INFO)
    action_logger.addHandler(file_handler)
    action_logger.addHandler(console_handler)
    
    return action_logger