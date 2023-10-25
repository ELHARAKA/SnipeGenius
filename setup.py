from setuptools import setup, find_packages

# Read the content of requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='SnipeGenius',
    version='1.0.2',
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'snipegenius = snipe:main',
        ],
    },
)