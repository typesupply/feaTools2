#!/usr/bin/env python

from distutils.core import setup

setup(name = "feaTools2",
      version = "0.1",
      description = "A library for interacting with GPOS and GSUB features.",
      author = "Tal Leming",
      author_email = "tal@typesupply.com",
      url = "https://github.com/typesupply/feaTools2",
      license = "MIT",
      packages = [
              "feaTools2",
              "feaTools2.writers",
              "feaTools2.parsers",
      ],
      package_dir = {"":"Lib"},
)
