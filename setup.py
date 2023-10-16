from setuptools import setup, find_packages

setup(
    name='SnipeGenius',
    version='1.0.1',
    packages=find_packages(),
    install_requires=[
        'web3',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'snipegenius = snipe:main',
        ],
    },
)
