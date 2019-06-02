# sbf viewer
Python3 GUI tool to analyse .sbf files (Sepentrio binary files).
#### Features:
Features of this are at the moment:
* Cython parsing (heavily inspired by: [pysbf][1])
* GUI with plotting window for L1-band and L2-band SNR (signal-to-noise ratio)
* Detects external events and plots them in the graph

#### Python3 Dependencies:
 * matplotlib
 * pathlib
 * PyQt5
 * Cython

#### Cython compilation:
To build the cython code, run: `python setup.py build_ext --inplace`

#### Analysing a sbf file:
To view a sbf file just run `python sbf_viewer.py <path_to_sbf_file>`

[1]: https://github.com/jashandeep-sohi/pysbf