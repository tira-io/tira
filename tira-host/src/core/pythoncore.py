#!/usr/bin/env python2
# -*- coding: utf8 -*-
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Steve Göring
"""
import os
import sys
import subprocess
import pickle

def colorred(m):
    return "\033[91m" + m + "\033[0m"


def colorblue(m):
    return "\033[94m" + m + "\033[0m"


def colorgreen(m):
    return "\033[92m" + m + "\033[0m"


def colorcyan(m):
    return "\033[96m" + m + "\033[0m"


def logInfo(msg):
    print(colorgreen("[INFO ] ") + str(msg))


def logError(msg):
    print(colorred("[ERROR] ") + str(msg))

def logTodo(msg):
    print(colorred("[TODO ] ") + colorred(str(msg)))


def logDebug(msg):
    print(colorblue("[DEBUG] ") + str(msg))


def logWarn(msg):
    print(colorcyan("[WARN]  ") + str(msg))


def scriptDir():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def shell_call(call):
    """
    Run a program via system call and return stdout + stderr.
    @param call programm and command line parameter list, e.g ["ls", "/"]
    @return stdout and stderr of programm call
    """
    try:
        output = subprocess.check_output(call, stderr=subprocess.STDOUT)
    except Exception, e:
        output = str(e.output)
    return output


def source(filename):
    """
    Load bash variables to a python map, like 'source' command in bash.
    @param filename: bash file to load
    """
    dump = "/usr/bin/python -c \
        'import os,pickle; \
        print pickle.dumps(os.environ)'"

    output = subprocess.check_output("/bin/bash -c \"set -a && source " +
        filename + " && " + dump + "\"", shell=True)

    env = pickle.loads(output)

    diff = set(env.keys()) - set(os.environ.keys())
    variables = {}
    for k in diff:
        variables[k] = env[k]
    return variables

def get_prog_name():
    """
    @return name of script
    """
    return os.path.basename(sys.argv[0])

if __name__ == "__main__":
    logError("Module is not standalone.")