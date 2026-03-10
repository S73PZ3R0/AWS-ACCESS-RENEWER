#!/usr/bin/env python3
import sys
import os

# Add 'src' to sys.path to allow importing the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from aws_access_renewer.__main__ import main

if __name__ == "__main__":
    main()
