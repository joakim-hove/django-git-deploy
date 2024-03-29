#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

requirements = ["pyaml"]

setup_requirements = [ ]

test_requirements = []

setup(
    author="Joakim Hove",
    author_email='joakim.hove@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Small package to create git hook for django deploy",
    scripts=["bin/deploy", "bin/make_hook"],
    install_requires=requirements,
    license="GNU General Public License v3",
    include_package_data=True,
    keywords='django_git_deploy',
    name='django_git_deploy',
    packages=find_packages(include=['django_git_deploy']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/joakim-hove/django_git_deploy',
    version='0.1.15',
    zip_safe=False,
)
