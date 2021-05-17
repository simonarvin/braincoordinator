#!/usr/bin/env python
from setuptools import setup, find_packages

install_requires = []

with open('requirements.txt') as f:
    for line in f.readlines():
        req = line.strip()
        if not req or req.startswith('#') or '://' in req:
            continue
        install_requires.append(req)

setup(
    name='braincoordinator',
    description='Brain Coordinator is a Python 3-based stereotaxic coordinator '
                'compatible with any stereotaxic atlas.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/simonarvin/braincoordinator',
    license='MIT',
    license_file='LICENSE',
    platforms='any',
    python_requires='>=3.7',
    version='0.11',
    entry_points={
        'console_scripts': [
            'braincoordinator=braincoordinator.run_coordinator:main'
        ]
    },
    packages=find_packages(include=["braincoordinator*"]),
    include_package_data=True,
    install_requires=install_requires,
    project_urls={
        "Documentation": "https://github.com/simonarvin/braincoordinator",
        "Source": "https://github.com/simonarvin/braincoordinator",
        "Tracker": "https://github.com/simonarvin/braincoordinator/issues"
    }
)
