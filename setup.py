from setuptools import setup, find_packages

setup(
    name='SnipeGenius',
    version='1.5.0',
    description='A sniping bot for detecting and trading new token pairs safely',
    url='https://github.com/ELHARAKA/SnipeGenius',
    author='Fahd El Haraka',
    author_email='fahd@web3dev.ma',
    license='https://github.com/ELHARAKA/SnipeGenius/blob/main/LICENSE',
    packages=find_packages(),
    install_requires=[
        'pyfiglet',
        'colorlog',
        'termcolor',
        'web3',
        'requests',
        'cryptography',
        'google-api-python-client==2.104.0',
        'pwinput'
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': [
            'snipegenius = snipe:main',
        ],
    },
)