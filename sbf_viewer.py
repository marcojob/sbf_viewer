"""Main script for sbf viewer tool"""

__author__ = 'Marco Job'
__license__ = 'GPL'

from argparse import ArgumentParser

from src.gui import run_GUI
from src.satellite import Satellite
from src import sat_statistics

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

    if not args.batch_processing:
        satellite = Satellite(args.sbf_file)
        run_GUI(satellite)
    else:
        sat_statistics.run(args.batch_processing)


if __name__ == "__main__":
    main()