# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
      name="pyrrha_ci",
      version="0.1",
      author_email="username@email.address",
      packages=['pyrrha_ci'],
      package_data={},
      description="correcteur d'annotations pyrrha",
      author="Marie-Caroline Schmied et Emilie Blotière",
      author_email="marie-caroline.schmied@chartes.psl.eu , emilie.blotiere@chartes.psl.eu",
      install_requires=['pyyaml', 'click'],
      entry_points={
        'console_scripts': ['pyrrha_ci = pyrrha_ci.code:test']
      }
)
