#! /bin/env python3
import os
import shutil

from setuptools import setup, find_packages
from setuptools.command.install import install


class PostInstallCommand(install):
    def run(self):
        install.run(self)
        for obj in ['build', 'dist', 'drt.egg-info']:
            if os.path.exists(obj):
                shutil.rmtree(obj)
            print("Removed {}".format(obj))


setup(
    name="swarm-cli",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click', 'docker', 'pyyaml', 'colorama', 'paramiko', 'coloredlogs', 'verboselogs','dotenv'
    ],
    entry_points={
        'console_scripts': [
            'swarm-cli = swarm_cli.cli:root'
        ]
    },
    author='Luca Nardelli',
    author_email='luca@sungazer.io',
    description="Docker swarm utility tool",

    cmdclass={
        'install': PostInstallCommand
    }
)
