#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup script for C. elegans Brain Simulator
Cross-platform installation for Windows, Linux, and macOS
"""

from setuptools import setup, find_packages
import os

# Read the long description from README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name='c_elegans_brain_simulator',
    version='1.0.0',
    description='Enhanced C. elegans neural network simulation with +10 neurons and +20 connections',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    author='OpenWorm Analysis Toolbox Extension',
    author_email='openworm@example.com',
    url='https://github.com/openworm/open-worm-analysis-toolbox',
    license='MIT',
    
    # Main simulation script
    py_modules=['c_elegans_brain_sim'],
    
    # Python version requirement
    python_requires='>=3.7',
    
    # Dependencies
    install_requires=[
        'numpy>=1.19.0',
    ],
    
    # Additional dependencies for optional features
    extras_require={
        'visualization': ['matplotlib>=3.3.0'],
        'analysis': ['scipy>=1.5.0', 'pandas>=1.1.0'],
        'dev': ['pytest>=6.0.0', 'black', 'flake8'],
    },
    
    # Console script entry point
    entry_points={
        'console_scripts': [
            'c-elegans-brain=c_elegans_brain_sim:main',
        ],
    },
    
    # Package metadata
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
    ],
    
    # Keywords
    keywords='c-elegans neuroscience simulation connectome neural-network brain',
    
    # Include package data
    package_data={
        '': ['*.json', '*.md', '*.txt'],
    },
    
    # Include all files in MANIFEST.in
    include_package_data=True,
)

print("\n" + "="*70)
print("C. ELEGANS BRAIN SIMULATOR - SETUP")
print("="*70)
print("\nInstallation options:")
print("  Basic: pip install .")
print("  Development: pip install -e .[dev]")
print("  With visualization: pip install .[visualization]")
print("\nAfter installation, run with:")
print("  c-elegans-brain")
print("  or")
print("  python c_elegans_brain_sim.py")
print("="*70)
