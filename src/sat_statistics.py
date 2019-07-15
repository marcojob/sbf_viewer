import logging

from pathlib import Path
from .satellite import Satellite

def run(directory):
    current_directory = get_valid_directory(directory)
    files = log_files(current_directory)
    for file in files:
        satellite = Satellite(file)

def log_files(directory):
    extensions = ['*.sbf']
    for extension in extensions:
        for file in directory.glob(r'**/{}'.format(extension)):
            if str('/.') not in str(file):  # Ignore hidden folders
                yield file

def get_valid_directory(directory):
    current_directory = Path(r'{}'.format(directory))

    if not current_directory.exists():
        logger.error('Error: Given directory does not exist')
        return None

    if current_directory.is_file():
        return Path(directory).parent

    return current_directory