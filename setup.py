from setuptools import setup

setup(
    name='servicePoints',
    version='0.1.0',
    packages=['servicePoints'],
    include_package_data=True,
    install_requires=[
        'arrow==0.15.5',
        'bs4==0.0.1',
        'Flask==2.3.2',
        'requests==2.22.0',
        'sh==1.12.14',
    ],
)
