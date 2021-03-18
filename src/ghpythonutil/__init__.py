"""
# -*- coding: utf-8 -*-
Custom Grasshopper utilities module

This module is designed to provide useful utility functions for users of the
ghPython custom scripting component.

Notes:
    Place lib folder in one of the following paths:
    
    # in a Grasshopper Python Script Editor:
    >>> import sys
    >>> for p in sys.path:
        print(path)
"""

__author__ = "Vincent Mai"
__version__ = "2021.03.15"

__all__ = [
    "treehandler",
    "contextmanager"
    ]

import treehandler
import contextmanager