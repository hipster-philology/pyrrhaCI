# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="Devoir_pyrrha",
    version="1.0",
    packages=find_packages(),
    description="correcteur d'annotations pyrrha",
    author="Marie-Caroline Schmied et Emilie Blotière",
    author_email="marie-caroline.schmied@chartes.psl.eu , emilie.blotiere@chartes.psl.eu",
    install_requires=['Click'],
    entry_points = {
        'console_scripts': [
            'test= Devoir_pyrrha.code:test',
        ],
    },
)
