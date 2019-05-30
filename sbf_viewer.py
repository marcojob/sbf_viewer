"""Main script for sbf viewer tool"""

__author__ = 'Marco Job'
__license__ = 'GPL'

from argparse import ArgumentParser

from sbf_gui import run_GUI
from sbf_satellite import Satellite


def main():
    parser = ArgumentParser(description='Tool used to analyse sbf files')
    parser.add_argument('sbf_file',
                        nargs='?',
                        help='Path to .sbf file to open',
                        type=str,
                        default='')
    args = parser.parse_args()

    run_GUI(args.sbf_file)


if __name__ == "__main__":
    main()
