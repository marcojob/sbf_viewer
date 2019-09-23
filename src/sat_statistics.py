import logging

import pandas as pd
import time
import pyulog

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
        data = data.append(pd.DataFrame(data=values, index=[idx]), sort=True)
    print('Processed files in {:.2f} s'.format(time.time()-starttime))
    csv_file = current_directory / Path('ppk_quality_output.csv')
    data.to_csv(csv_file)


def event_run(file):
    TRIG_DET_STR = 'trigger detected [ms]'
    TRIG_DET_DIF_STR = 'trigger detected diff [ms]'
    TRIG_CMD_STR = 'trigger commanded [ms]'
    TRIG_CMD_DIF_STR = 'trigger commanded diff [ms]'
    csv_file = Path(file).parent / Path('events.csv')
    data = pd.DataFrame()

    events_cmded = list()
    ulog_folder = Path(file).parents[1]
    for ulog_file in ulog_files(ulog_folder):
        print('processing {}'.format(ulog_file))
        try:
            ulog = pyulog.ULog(str(ulog_file))
        except Exception as e:
            print(e)
            continue

        for key in ulog.logged_messages_obc:
            data_list = ulog.logged_messages_obc[key]
            for elem in data_list:
                if 'In _trigger_test_image' in elem.message:
                    events_cmded.append(elem.timestamp/1000)

    data[TRIG_CMD_STR] = pd.Series(events_cmded)
    data[TRIG_CMD_DIF_STR] = abs(data[TRIG_CMD_STR] - data[TRIG_CMD_STR].shift(1))

    satellite = Satellite()
    print('processing {}'.format(file))
    satellite.load_file(Path(file))
    data[TRIG_DET_STR] = pd.Series(satellite.events['tow'])
    data[TRIG_DET_DIF_STR] = abs(data[TRIG_DET_STR] - data[TRIG_DET_STR].shift(1))

    data.to_csv(csv_file)


def log_files(directory):
    extensions = ['*.sbf']
    for extension in extensions:
        for file in directory.glob(r'**/{}'.format(extension)):
            if str('/.') not in str(file) and not 'Base' in str(file) and not 'ForwardProcessed' in str(file):  # Ignore hidden folders
                yield file


def ulog_files(directory):
    extensions = ['*.ulg']
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
