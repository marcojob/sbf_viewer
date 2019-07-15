from . import pysbf
import matplotlib.pyplot as plt

from pathlib import Path
from numpy import mean
import pandas as pd

DEFAULT_VALUE = 'N/A'
MIN_LENGTH = 7


class Satellite:
    def __init__(self, sbf_file):
        self.sbf_file = sbf_file
        self.signals = {}
        self.events = {'tow': list()}
        self.dict_df = {'1': dict(), '2': dict()}
        self.means = {'1': list(), '2': list()}
        self.sig_num_ref = pysbf.sig_num_ref
        self.load_file(sbf_file)
        self.to_dict_df()
        self.update_sorted_mean_list(band='1')
        self.update_sorted_mean_list(band='2')

    def load_file(self, sbf_file):
        sbf_file = Path(sbf_file)
        self.signals = {}
        if sbf_file.is_file():
            with sbf_file.open() as sbf_fobj:
                for blockName, block in pysbf.load(sbf_fobj, blocknames={'MeasEpoch_v2', 'ExtEvent'}):
                    import pdb
                    if blockName == 'MeasEpoch_v2':
                        for meas in block['Type_1']:
                            self.update_signals(block['TOW'], block['WNc'], meas['SVID'],
                                                meas['Type'], meas['CN0'], meas['LockTime'])
                            for nested_entry in meas['Type_2']:
                                self.update_signals(block['TOW'], block['WNc'], meas['SVID'],
                                                    nested_entry['Type'], nested_entry['CN0'], nested_entry['LockTime'])

                    elif blockName == 'ExtEvent':
                        self.update_events(block['TOW'], block['WNc'])

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

    def to_dict_df(self):
        for num in self.signals:
            if self.sig_num_ref[num]['band'] == 1 and self.sig_num_ref[num]['en'] == True:
                for sat in self.signals[num]:
                    self.dict_df['1'][sat] = pd.DataFrame(data=self.signals[num][sat]['snr'],
                                                          index=self.signals[num][sat]['tow'])
            elif self.sig_num_ref[num]['band'] == 2 and self.sig_num_ref[num]['en'] == True:
                for sat in self.signals[num]:
                    self.dict_df['2'][sat] = pd.DataFrame(data=self.signals[num][sat]['snr'],
                                                          index=self.signals[num][sat]['tow'])

    def update_sorted_mean_list(self, band):
        if self.events['tow'] == list():
            for sat in self.dict_df[band]:
                values = self.dict_df[band].get(sat, pd.Series())
                if values.empty:
                    self.means[band].append(0.0)
                else:
                    value = values.mean()
                    self.means[band].append(value[0])
        else:
            for sat in self.dict_df[band]:
                self.means[band].append(self.get_event_mean(self.dict_df[band][sat], self.events))
        self.means[band].sort(reverse=True)

    def get_event_mean(self, sat, events):
        mean_list = list()
        for trig in events['tow']:
            trig_alt = int(trig/100)*100
            value_event = sat.loc[sat.index == trig_alt]
            if not value_event.empty:
                val_list = value_event[0].tolist()
                mean_list.append(val_list[0])
        if not mean_list == list():
            return mean(mean_list)
        else:
            return 0

    def get_max_mean(self, band):
        if self.means[band] == list():
            return DEFAULT_VALUE
        return self.means[band][0]

    def get_top_mean(self, band):
        length = MIN_LENGTH if len(self.means[band]) > MIN_LENGTH else len(self.means[band])
        return length, mean(self.means[band][:length])

    def get_n_thresh(self, means, threshold):
        return sum(i >= threshold for i in means)

    def update_events(self, tow, wnc):
        self.events['tow'].append(tow)

    def get_band(self, sig_type):
        return sig_type & 0b00011111

    def get_snr(self, cn0, sig_num):
        if sig_num == 1 or sig_num == 2:
            return cn0*0.25
        else:
            return cn0*0.25+10.0

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
