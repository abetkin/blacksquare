from setuptools import setup, find_packages
import codecs
import os
import re


with codecs.open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="patched",
    install_requires=[
        "IPython",
    ],

    # There are various approaches to referencing the version. For a discussion,
    # see http://packaging.python.org/en/latest/tutorial.html#version
    version='0.1',

    description="Smart patching, logging, debug",
    long_description='',

    # The project URL.
    url='https://github.com/abetkin/patched',

    # Author details
    author='abetkin',
    author_email='abvit89@gmail.com',

    # Choose your license
    license='MIT',

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    # What does your project relate to?
    keywords='patching',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages.
    packages=["patched"],

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed.
)
