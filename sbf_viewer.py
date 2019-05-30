import pysbf
import matplotlib.pyplot as plt


def run():
    satellite = Satellite()
    with open('./ppk_0.sbf') as sbf_fobj:
        for blockName, block in pysbf.load(sbf_fobj, blocknames={'MeasEpoch_v2'}):
            for meas in block['Type_1']:
                satellite.update(block['TOW'], block['WNc'], meas['SVID'], meas['Type'], meas['CN0'], meas['LockTime'])
    satellite.plot_all()

class Satellite:
    def __init__(self):
        self.signals = {}

    def update(self, tow, wnc, svid, sig_type, cn0, locktime):
        sig_num = self.get_band(sig_type)
        snr = self.get_snr(cn0, sig_num)
        if not sig_num in self.signals.keys():
            self.signals[sig_num] = {}

        if not svid in self.signals[sig_num].keys():
            self.signals[sig_num][svid] = {
                "tow": [],
                "wnc": [],
                "snr": [],
                "locktime": []
            }

        self.signals[sig_num][svid]["tow"].append(tow)
        self.signals[sig_num][svid]["wnc"].append(wnc)
        self.signals[sig_num][svid]["snr"].append(snr)
        self.signals[sig_num][svid]["locktime"].append(locktime)

    def plot_all(self):
        for sig_num in self.signals:
            for sat in self.signals[sig_num]:
                plt.plot(self.signals[sig_num][sat]['tow'], self.signals[sig_num][sat]['snr'])
        plt.show()

    def get_band(self, sig_type):
        return sig_type & 0b00011111

    def get_snr(self, cn0, sig_num):
        return cn0*0.25 if sig_num == 1 or sig_num == 2 else cn0*0.25+10.0


if __name__ == "__main__":
    run()
