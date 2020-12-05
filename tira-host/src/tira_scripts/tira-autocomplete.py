#!/usr/bin/env python2
# -*- coding: utf8 -*-
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Steve Göring
"""
import sys
import os
tiraargs = __import__("tira-args")
tirasetup = __import__("tira-setup")


def printout(commands):
    """
    Printout keys of command dictionary.
    """
    keys = []
    for i in commands:
        keys.append(i)
    print(" ".join(keys))


def main(args):
    """
    Printout list of all subscripts.
    This script is usesd by bash auto complete definition
    to extract possible command completions.
    """

    if len(args) != 0:
        # printout admin parameters
        printout(tirasetup.getcommands())
        return

    printout(tiraargs.getcommands())

if __name__ == "__main__":
    main(sys.argv[1:])
