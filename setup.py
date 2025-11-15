from setuptools import setup, find_packages

setup(
    name='mapcat',
    version='0.1.0',
    description='CLI tool to visualize geospatial commands on a Leaflet map',
    author='Maxim Tkachenko',
    packages=find_packages(),
    package_data={
        'mapcat': ['static/*'],
    },
    include_package_data=True,
    install_requires=[
        'websockets',
    ],
    entry_points={
        'console_scripts': [
            'mapcat=mapcat.main:main',
        ],
    },
    python_requires='>=3.11',
)
