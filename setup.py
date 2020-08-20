from setuptools import setup, find_packages

setup(
    name='pensieve',
    version='0.1.0',
    packages=['pensieve'],
    install_requires=['pyyaml'],
    entry_points={
        'console_scripts': [
            'pensieve = pensieve:main'
        ]
    }
)

