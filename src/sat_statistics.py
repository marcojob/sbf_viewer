import logging

import pandas as pd
import time
import webbrowser
import pickle
import re

from pathlib import Path
from .satellite import Satellite
from googleapiclient import discovery
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.service_account import Credentials

def get_google_sheets():

    creds = get_production_credentials()

    if creds is not None:
        resource = discovery.build(serviceName='sheets', version='v4', credentials=creds, cache_discovery=False)
        return resource.spreadsheets()
    else:
        return None


def get_production_credentials():
    """Production sheets are used for inop and need special access rights.
    Google sheets authentication is done via using a credentials file. Download the credentials.json from 
    https://developers.google.com/sheets/api/quickstart/python
    Put it into the resources folder and allow access when running for the first time.
    """

    creds = None
    # The file token.pickle stores the user's access and refresh tokens,
    # and is created automatically when the authorization flow completes for the first time
    token_pickle_path = Path('token.pickle')
    credentials_path =  Path('credentials.json')
    if not credentials_path.exists():
        webbrowser.open('https://developers.google.com/sheets/api/quickstart/python')
        print('1) Click on the button "Enable the Google Sheets API')
        print('2) Click on "Download client configuration" and store credentials.json in resources folder in WiE repository')
        print('3) Install additional python packages: pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib')
        input('When all done, click enter to proceed')
    if credentials_path.exists() and not token_pickle_path.exists():
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server()
            with token_pickle_path.open(mode='wb') as token:
                pickle.dump(creds, token)
    
    if  token_pickle_path.exists():
        with token_pickle_path.open(mode='rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
    if creds is None:
        print('Failed to get production credentials')
    return creds

def get_telemetry_and_hw_version_per_plane():
        """Retrieve the hw version and telemetry frequency details per plane from the plane overview sheet"""
        google_sheets = get_google_sheets()

        PLANE_OVERVIEW_SHEET_ID = '1JRH9OXNGmRaYcmztMHTl51jukus4QdLRdvBsZ19g_D4'
        RANGE = 'Plane Details!A7:C'

        result = google_sheets.values().get(spreadsheetId=PLANE_OVERVIEW_SHEET_ID,
                                                 range=RANGE,
                                                 valueRenderOption='FORMATTED_VALUE').execute()
        rows = result.get('values', [])

        # Sheets API ignores empty trailing cells, leading to non-uniform length inner lists
        # We process it with dataframe to append None to such lists to keep rest of the processing easy
        df = pd.DataFrame(rows)
        df_replace = df.replace([''], [None])
        processed_rows = df_replace.values.tolist()

        hw_ver_and_telem_dict = {}
        for plane_id, hw_version, telemetry in processed_rows:
            hw_ver_and_telem_dict[str(plane_id)] = [str(hw_version), str(telemetry)]
        return hw_ver_and_telem_dict

def add_info(df, info_dict):
    df['HW Ver'] = 'N/A'
    df['Flight Day'] = 'N/A'
    df['Plane ID'] = 'N/A'
    for folder_name in df.index:
        match = re.match('.*/(20[0-9]{6})_.*/([0-9]{4})_.*', folder_name)
        if match:
            flight_day = match.group(1)
            plane_id = match.group(2)
            df.loc[folder_name, 'Flight Day'] = flight_day
            df.loc[folder_name, 'Plane ID'] = plane_id
            if plane_id in info_dict.keys():
                df.loc[folder_name, 'HW Ver'] = info_dict.get(plane_id)[0]

    return df

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
    print('Downloading hadware info from gsheet')
    hw_ver_and_telem_dict = get_telemetry_and_hw_version_per_plane()
    data  = add_info(data , hw_ver_and_telem_dict)
    csv_file = current_directory / Path('ppk_quality_output.csv')
    data.to_csv(csv_file)

def log_files(directory):
    extensions = ['*.sbf']
    for extension in extensions:
        for file in directory.glob(r'**/{}'.format(extension)):
            if str('/.') not in str(file) and not 'Base' in str(file) and not 'ForwardProcessed' in str(file):  # Ignore hidden folders
                yield file

def get_valid_directory(directory):
    current_directory = Path(r'{}'.format(directory))

    if not current_directory.exists():
        print('Error: Given directory does not exist')
        return None

    if current_directory.is_file():
        return Path(directory).parent

    return current_directory