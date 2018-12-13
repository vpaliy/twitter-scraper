from setuptools import setup, find_packages
import os
import re

base_path = os.path.dirname(__file__)

with open(os.path.join(base_path, 'tweebot', '__init__.py')) as fp:
  VERSION = re.compile(r".*__version__ = '(.*?)'", re.S).match(fp.read()).group(1)

version = VERSION

requires = [
  'requests>=2.18.4',
  'six>=1.11.0',
  'SQLAlchemy>=1.1.14',
  'urllib3>=1.22',
  'beautifulsoup4>=4.4.0'
]

packages = [
  'tweebot'
]

setup(
    name='tweebot',
    version=version,
    description='Twitter bot',
    author='Vasyl Paliy',
    author_email='vpaliy97@gmail.com',
    url='https://github.com/thevpaliy/twitter-santa',
    license='MIT',
    python_requires=">=3.0",
    packages=packages,
    install_requires=requires,
    use_2to3=True,
    include_package_data=True,
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
