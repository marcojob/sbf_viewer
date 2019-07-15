from . import pysbf
import matplotlib.pyplot as plt

from pathlib import Path
import pandas as pd

class Satellite:
    def __init__(self, sbf_file):
        self.signals = {}
        self.events = {
            'tow': []
        }
        self.dict_df_1, self.dict_df_2 = dict(), dict()
        self.sig_num_ref = pysbf.sig_num_ref
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

        self.to_dict_df()

    def to_dict_df(self):
        for num in self.signals:
            print(self.sig_num_ref[num])
            if self.sig_num_ref[num]['band'] == 1:
                for sat in self.signals[num]:
                    print(sat)
                    self.dict_df_1[sat] = pd.DataFrame(data=self.signals[num][sat]['snr'], 
                                                  index=self.signals[num][sat]['tow'])
            elif self.sig_num_ref[num]['band'] == 2:
                for sat in self.signals[num]:
                    print(sat)
                    self.dict_df_2[sat] = pd.DataFrame(data=self.signals[num][sat]['snr'],
                                                  index=self.signals[num][sat]['tow'])

    def update_signals(self, tow, wnc, svid, sig_type, cn0, locktime):
        sig_num = self.get_band(sig_type)
        svid_offset = self.get_svid(svid)
        snr = self.get_snr(cn0, sig_num)
        if not sig_num in self.signals.keys():
            self.signals[sig_num] = {}

        if not svid_offset in self.signals[sig_num].keys():
            self.signals[sig_num][svid_offset] = {
                'snr': [],
                'tow': []
            }

        self.signals[sig_num][svid_offset]['snr'].append(snr)
        self.signals[sig_num][svid_offset]['tow'].append(tow)

    def update_events(self, tow, wnc):
        self.events['tow'].append(tow)

    def get_band(self, sig_type):
        return sig_type & 0b00011111

    def get_snr(self, cn0, sig_num):
        return cn0*0.25 if sig_num == 1 or sig_num == 2 else cn0*0.25+10.0

    def get_svid(self, svid):
        '''Table 4.1.9'''
        if svid >= 1 and svid <= 37:
            return 'G{:02d}'.format(svid)
        elif svid >= 38 and svid <= 61:
            return 'R{:02d}'.format(svid-37)
        elif svid >= 63 and svid <= 68:
            return 'R{:02d}'.format(svid-38)
        elif svid >= 71 and svid <= 106:
            return 'E{:02d}'.format(svid-70)
        elif svid >= 120 and svid <= 140:
            return 'S{:02d}'.format(svid-100)
        elif svid >= 141 and svid <= 177:
            return 'C{:02d}'.format(svid-40)
        elif svid >= 181 and svid <= 187:
            return 'J{:02d}'.format(svid-180)
        elif svid >= 191 and svid <= 197:
            return 'I{:02d}'.format(svid-190)
        elif svid >= 198 and svid <= 215:
            return 'S{:02d}'.format(svid-157)
        return svid