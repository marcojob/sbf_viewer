"""Main script for sbf viewer tool"""

__author__ = 'Marco Job'
__license__ = 'GPL'

from argparse import ArgumentParser

from src.gui import run_GUI
from src.satellite import Satellite

import time


def main():
    parser = ArgumentParser(description='Tool used to analyse sbf files')
    parser.add_argument('sbf_file',
                        nargs='?',
                        help='Path to .sbf file to open',
                        type=str,
                        default='')
    parser.add_argument('--batch_processing', '-b',
                        help='Path to directory on which to perform batch processing. If given, overrides any GUI commands',
                        type=str)
    args = parser.parse_args()

    starttime = time.time()
    satellite = Satellite(args.sbf_file)
    print('Loaded file in {:.2f} s'.format(time.time()-starttime))
    starttime = time.time()
    run_GUI(satellite)
    print('Plotted file in {}'.format(time.time()-starttime))


if __name__ == "__main__":
    main()
