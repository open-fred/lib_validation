from setuptools import setup

setup(name='lib_validation',
      version='0.0.1',
      description='Scripts to validate the pvlib and windpowerlib.',
      url='http://github.com/open-fred/lib_validation',
      author='oemof developing group',
      author_email='',
      license='GPL3',
      packages=[],
      zip_safe=False,
      install_requires=['pandas',
                        'matplotlib',
                        'xarray',
                        'pvlib >= 0.5.0',
                        'windpowerlib >= 0.0.6'])