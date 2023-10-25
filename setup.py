from setuptools import setup, find_packages

# Read the content of requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='SnipeGenius',
    version='1.5.0',
    description='A sniping bot for detecting and trading new token pairs safely',
    url='https://github.com/ELHARAKA/SnipeGenius',
    author='Fahd El Haraka',
    author_email='fahd@web3dev.ma',
    license='https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE',
    packages=find_packages(),
    install_requires=requirements,
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'snipegenius = snipe:main',
        ],
    },
)