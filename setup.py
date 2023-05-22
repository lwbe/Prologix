from setuptools import setup


setup(
    name = 'prologix',
    version = '1.0',
    py_modules = ['prologix'],
    install_requires=[
        'pyserial',
    ],
)
