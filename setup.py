from distutils.core import setup, Extension
from Cython.Distutils import build_ext

def Main(cythonize=False):
    ext_modules = [
        Extension('pysbf.sbf', ['src/pysbf/sbf.pyx', 'src/pysbf/c_crc.c']),
        Extension('pysbf.blocks', ['src/pysbf/blocks.py']),
        Extension('pysbf.parsers', ['src/pysbf/parsers.pyx'])
    ]
    cmdclass = {'build_ext': build_ext}

    setup(name='pysbf',
        packages = ['src/pysbf'],
        cmdclass = cmdclass,
        ext_modules = ext_modules
    )

if __name__ == '__main__':
 Main()
