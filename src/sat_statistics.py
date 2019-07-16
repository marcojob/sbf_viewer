import logging

import pandas as pd
import time

from pathlib import Path
from .satellite import Satellite

def run(directory):
    satellite = Satellite()
    current_directory = get_valid_directory(directory)
    data = pd.DataFrame()
    files = log_files(current_directory)
    starttime = time.time()
    for file in files:
        print('Processing {}'.format(str(file)))
        satellite.load_file(file)
        idx, values = satellite.check()
        data = data.append(pd.DataFrame(data=values, index=[idx]))
    print('Processed files in {:.2f} s'.format(time.time()-starttime))
    csv_file = current_directory / Path('ppk_quality_output.csv')
    data.to_csv(csv_file)

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