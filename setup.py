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
