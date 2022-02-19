#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [ ]

setup_requirements = [ ]

test_requirements = [ ]

setup(
    author="4training",
    author_email='pywikitools@4training.net',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Python tools for mediawiki with the Translate plugin (some based on pywikibot)",
    entry_points={
        'console_scripts': [
            'pywikitools=pywikitools.cli:main',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pywikitools',
    name='pywikitools',
    packages=find_packages(include=['pywikitools', 'pywikitools.*']),
    setup_requires=setup_requirements,
    test_suite='pywikitools.test',
    tests_require=test_requirements,
    url='https://github.com/4training/pywikitools',
    version='0.1.0',
    zip_safe=False,
)
