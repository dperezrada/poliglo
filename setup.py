from setuptools import setup, find_packages
import sys, os

version = '0.0.1'

setup(name='poliglo-server',
      version=version,
      description="Poliglo server",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Daniel P\xc3\xa9rez Rada',
      author_email='dperezrada@gmail.com',
      url='https://github.com/dperezrada/poliglo',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
            'flask',
            'flask-cors',
            'poliglo',
            'tornado'
      ],
      tests_require=['nose'],
      test_suite="tests",
      entry_points={
            'console_scripts': [
                  'poliglo_server = poliglo_server:start_server',
            ],
      },
)
