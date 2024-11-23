import sys
import re
from datetime import datetime

from loguru import logger


def logging_setup():
    format_info = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <blue>{level: <7}</blue> | <level>{message}</level>"
    format_error = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <blue>{level: <7}</blue> | " \
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    file_path = r"logs/"
    
    logger.remove()

    # Log to file with a size limit of 1GB
    logger.add(
        file_path + f"log_{datetime.now().strftime('%Y-%m-%d')}.log", 
        colorize=True,
        format=format_info,
        rotation="1 GB"  # Rotate log file when it reaches 1GB
    )

    # Log to stdout
    logger.add(
        sys.stdout, 
        colorize=True,
        format=format_info, 
        level="INFO"
    )


def clean_brackets(raw_str):
    clean_text = re.sub(brackets_regex, '', raw_str)
    return clean_text


brackets_regex = re.compile(r'<.*?>')

logging_setup()
