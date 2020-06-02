# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
      name="pyrrha_ci",
      version="0.0.1",
      author_email="marie-caroline.schmied@chartes.psl.eu , emilie.blotiere@chartes.psl.eu, thibault.clerice@chartes.psl.eu",
      packages=['pyrrha_ci'],
      package_data={},
      description="correcteur d'annotations pyrrha",
      author="Marie-Caroline Schmied, Emilie Blotière, Thibault Clérice",
      install_requires=['pyyaml', 'click', 'regex'],
      entry_points={
        'console_scripts': ['pyrrha-ci = pyrrha_ci.code:test']
      }
)
