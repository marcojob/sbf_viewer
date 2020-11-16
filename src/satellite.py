from pysbf import sbf
from pathlib import Path
from numpy import mean
from .sbf_map import sig_num_ref, gain_num_ref

import pandas as pd
import matplotlib.pyplot as plt

DEFAULT_VALUE = 'N/A'
MIN_LENGTH = 7
BEST_L1 = 43
GOOD_L1 = 40
BEST_L2 = 36
GOOD_L2 = 30


class Satellite:
    def __init__(self, sbf_file=None):
        self.sig_num_ref = sig_num_ref
        self.gain_num_ref = gain_num_ref
        if sbf_file:
            self.load_file(sbf_file)

    def load_file(self, sbf_file):
        # Reset all counters
        self.signals = dict()
        self.gain_signals = dict()
        self.events = {'tow': list()}
        self.dict_df = {'1': dict(), '2': dict()}
        self.means = {'1': list(), '2': list()}
        self.mission_min_tow = 0.0
        self.mission_max_tow = 0.0
        self.n_ext_events = 0


        # Process file
        self.sbf_file = Path(sbf_file)
        if self.sbf_file.is_file():
            with self.sbf_file.open() as sbf_fobj:
                for blockName, block in sbf.load(sbf_fobj, blocknames={'MeasEpoch_v2', 'ExtEvent', 'ReceiverStatus_v2'}):
                    if blockName == 'MeasEpoch_v2':
                        for meas in block['Type_1']:
                            self.update_signals(block['TOW'], block['WNc'], meas['SVID'],
                                                meas['Type'], meas['CN0'], meas['LockTime'])
                            for nested_entry in meas['Type_2']:
                                self.update_signals(block['TOW'], block['WNc'], meas['SVID'],
                                                    nested_entry['Type'], nested_entry['CN0'], nested_entry['LockTime'])

                    elif blockName == 'ExtEvent':
                        self.update_events(block['TOW'], block['WNc'])
                        self.n_ext_events = self.n_ext_events + 1
                    elif blockName == 'ReceiverStatus_v2':
                        for meas in block['AGCData']:
                            self.update_gain(block['TOW'], block['WNc'], meas['FrontendID'], meas['Gain'])
        self.to_dict_df()
        self.update_sorted_mean_list(band='1')
        self.update_sorted_mean_list(band='2')

    def check(self):
        len_top_1, val_top_1 = self.get_top_mean('1')
        len_top_2, val_top_2 = self.get_top_mean('2')
        checks = {
            'Best sat. L1 [dB-Hz]': self.get_max_mean('1'),
            'Best sat. L2 [dB-Hz]': self.get_max_mean('2'),
            'Avg. of top L1 sat. [dB-Hz]': val_top_1,
            'Len. of top L1 sat. [ ]': len_top_1,
            'Avg. of top L2 sat. [dB-Hz]': val_top_2,
            'Len. of top L2 sat. [ ]': len_top_2,
            'Inop: n sat. over {} dB-Hz L1 []'.format(BEST_L1): self.get_n_thresh('1', BEST_L1),
            'Inop: n sat. over {} dB-Hz L1 []'.format(GOOD_L1): self.get_n_thresh('1', GOOD_L1),
            'Inop: n sat. over {} dB-Hz L2 []'.format(BEST_L2): self.get_n_thresh('2', BEST_L2),
            'Inop: n sat. over {} dB-Hz L2 []'.format(GOOD_L2): self.get_n_thresh('2', GOOD_L2),
            'Num. of ExtEvent': self.n_ext_events,
            'Mission duration [min]': self.get_mission_duration()
        }
        checks = self.checks_gain(checks)
        return str(self.sbf_file), checks

    def checks_gain(self, checks):
        for sig_num in self.gain_signals.keys():
            col_str = 'Frontend gain avg: {}'.format(self.gain_num_ref[sig_num]['sig_type'])
            checks[col_str] = mean(self.gain_signals[sig_num]['gain'])
        return checks

    def update_signals(self, tow, wnc, svid, sig_type, cn0, locktime):
        sig_num = self.get_band(sig_type)
        svid_offset = self.get_svid(svid)
        snr = self.get_snr(cn0, sig_num)
        if not sig_num in self.signals.keys():
            self.signals[sig_num] = dict()

        if not svid_offset in self.signals[sig_num].keys():
            self.signals[sig_num][svid_offset] = {
                'snr': list(),
                'tow': list()
            }
        self.signals[sig_num][svid_offset]['snr'].append(snr)
        self.signals[sig_num][svid_offset]['tow'].append(tow)
        if tow < self.mission_min_tow:
            self.mission_min_tow = tow
        if tow > self.mission_max_tow:
            self.mission_max_tow = tow

    def update_gain(self, tow, wnc, frontend_id, gain):
        sig_num = self.get_band(frontend_id)
        if not self.gain_num_ref[sig_num]['en']:
            return
        if not sig_num in self.gain_signals.keys():
            self.gain_signals[sig_num] = {'tow': list(), 'gain': list()}
        self.gain_signals[sig_num]['tow'].append(tow)
        self.gain_signals[sig_num]['gain'].append(gain)

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

    def get_n_thresh(self, band, threshold):
        return sum(i >= threshold for i in self.means[band])

    def update_events(self, tow, wnc):
        self.events['tow'].append(tow)

    def get_band(self, sig_type):
        return sig_type & 0b00011111

    def get_snr(self, cn0, sig_num):
        if sig_num == 1 or sig_num == 2:
            return cn0*0.25
        else:
            return cn0*0.25+10.0

    def get_mission_duration(self):
        return round((self.mission_max_tow-self.mission_min_tow) / (60. * 1.0e6))

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
