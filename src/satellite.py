from . import pysbf
import matplotlib.pyplot as plt

from pathlib import Path
from numpy import mean
import pandas as pd

class Satellite:
    def __init__(self, sbf_file):
        self.sbf_file = sbf_file
        self.signals = {}
        self.events = {
            'tow': []
        }
        self.dict_df_1 = dict()
        self.dict_df_2 = dict()
        self.means_1 = list()
        self.means_2 = list()
        self.mean_summary_1 = dict()
        self.mean_summary_2 = dict()
        self.sig_num_ref = pysbf.sig_num_ref
        self.load_file(sbf_file)
        self.to_dict_df()
        self.get_means()

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
                    self.dict_df_1[sat] = pd.DataFrame(data=self.signals[num][sat]['snr'],
                                                       index=self.signals[num][sat]['tow'])
            elif self.sig_num_ref[num]['band'] == 2 and self.sig_num_ref[num]['en'] == True:
                for sat in self.signals[num]:
                    self.dict_df_2[sat] = pd.DataFrame(data=self.signals[num][sat]['snr'],
                                                       index=self.signals[num][sat]['tow'])

    def get_means(self):
        LEN_MIN = 7
        if self.events['tow'] == list():
            for sat in self.dict_df_1:
                value = self.dict_df_1[sat].mean()
                self.means_1.append(value[0])
            for sat in self.dict_df_2:
                value = self.dict_df_1[sat].mean()
                self.means_2.append(value[0])
        else:
            for sat in self.dict_df_1:
                self.means_1.append(self.get_event_mean(self.dict_df_1[sat], self.events))
            for sat in self.dict_df_2:
                self.means_2.append(self.get_event_mean(self.dict_df_2[sat], self.events))
        self.means_1.sort(reverse=True)
        self.means_2.sort(reverse=True)

        self.mean_summary_1['max'] = self.means_1[0]
        self.mean_summary_2['max'] = self.means_2[0]

        if len(self.means_1) < LEN_MIN:
            self.mean_summary_1['val'] = mean(self.means_1)
            self.mean_summary_1['len'] = len(self.means_1)
        else:
            self.mean_summary_1['val'] = mean(self.means_1[:LEN_MIN])
            self.mean_summary_1['len'] = LEN_MIN

        if len(self.means_2) < LEN_MIN:
            self.mean_summary_2['val'] = mean(self.means_2)
            self.mean_summary_2['len'] = len(self.means_2)
        else:
            self.mean_summary_2['val'] = mean(self.means_2[:LEN_MIN])
            self.mean_summary_2['len'] = LEN_MIN

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
