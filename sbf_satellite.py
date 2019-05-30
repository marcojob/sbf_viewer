import pysbf
import matplotlib.pyplot as plt
import datetime
import calendar

from pathlib import Path

class Satellite:
    def __init__(self, sbf_file):
        self.datetimeformat = "%Y-%m-%d %H:%M:%S.%f"
        self.epoch = datetime.datetime.strptime("1980-01-06 00:00:00.000", self.datetimeformat)
        self.signals = {}
        self.sig_num_ref = pysbf.sig_num_ref

        self.events = {
            "datetime": [],
        }
        self.load_file(sbf_file)

    def load_file(self, sbf_file):
        sbf_file = Path(sbf_file)
        self.signals = {}
        if sbf_file.is_file():
            with sbf_file.open() as sbf_fobj:
                for blockName, block in pysbf.load(sbf_fobj, blocknames={'MeasEpoch_v2', 'ExtEvent'}):
                    if blockName == 'MeasEpoch_v2':
                        for meas in block['Type_1']:
                            self.update_signals(block['TOW'], block['WNc'], meas['SVID'],
                                                meas['Type'], meas['CN0'], meas['LockTime'])
                    elif blockName == 'ExtEvent':
                        self.update_events(block['TOW'], block['WNc'])

    def update_signals(self, tow, wnc, svid, sig_type, cn0, locktime):
        sig_num = self.get_band(sig_type)
        snr = self.get_snr(cn0, sig_num)
        if not sig_num in self.signals.keys():
            self.signals[sig_num] = {}

        if not svid in self.signals[sig_num].keys():
            self.signals[sig_num][svid] = {
                "snr": [],
                "locktime": [],
                "datetime": []
            }

        self.signals[sig_num][svid]["snr"].append(snr)
        self.signals[sig_num][svid]["locktime"].append(locktime)
        self.signals[sig_num][svid]["datetime"].append(self.get_time(wnc, tow))

    def update_events(self, tow, wnc):
        self.events["datetime"].append(self.get_time(wnc, tow))

    def get_band(self, sig_type):
        return sig_type & 0b00011111

    def get_snr(self, cn0, sig_num):
        return cn0*0.25 if sig_num == 1 or sig_num == 2 else cn0*0.25+10.0

    def get_time(self, wnc, tow):
        elapsed = datetime.timedelta(days=(wnc*7), seconds=(tow / 1000), milliseconds=(tow - (tow / 1000)*1000))
        xc_str = datetime.datetime.strftime(self.epoch + elapsed, self.datetimeformat)
        xc_dt = datetime.datetime.strptime(xc_str, "%Y-%m-%d %H:%M:%S.%f")
        return xc_dt