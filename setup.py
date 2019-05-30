#This file is part of "pysbf".
#Copyright (c) 2013, Jashandeep Sohi (jashandeep.s.sohi@gmail.com)
#
#"pysbf" is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#"pysbf" is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup, Extension
from Cython.Distutils import build_ext

def Main(cythonize=False):
    ext_modules = [
        Extension('pysbf.sbf', ['pysbf/sbf.pyx', 'pysbf/c_crc.c']),
        Extension('pysbf.blocks', ['pysbf/blocks.py']),
        Extension('pysbf.parsers', ['pysbf/parsers.pyx'])
    ]
    cmdclass = {'build_ext': build_ext}

    setup(name='pysbf',
        packages = ['pysbf'],
        cmdclass = cmdclass,
        ext_modules = ext_modules
    )

if __name__ == '__main__':
 Main()
