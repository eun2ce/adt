#!/usr/bin/python
# _*_ coding: utf-8 _*_

import os

from setuptools import setup, find_packages
from setuptools.command.install import install

name = "adt"


class Post(install):
    def run(self):
        install.run(self)


with open("requirements.txt", "r") as f:
    required = f.read().splitlines()

setup(
    name=name,
    version="1.0.1-dev0",
    author="eun2ce",
    description="joeun2ce@gmail.com",
    packages=find_packages(exclude=["tests*"]),
    package_data={name: ["config_file.yaml"]},
    include_package_data=True,
    install_requires=required,
    entry_points={"console_scripts": ["adt=adt.main:main"]},
    classifiers=["Programming Language :: Python :: 3.9"],
    zip_safe=True,
    scripts=[os.path.join("adt", "post_install.py")],
    cmdclass={"install": Post},
)
