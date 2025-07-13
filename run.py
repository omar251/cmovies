#!/usr/bin/env python3
"""
Entry point script for cmovies.

This script provides a simple way to run the cmovies CLI without installing the package.
"""

import sys
from cmovies.cli import main

if __name__ == "__main__":
    sys.exit(main())