#!/usr/bin/env python2
# -*- coding: utf8 -*-
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Steve Göring
"""
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/core/")

from pythoncore import *


def usage():
    prog = get_prog_name()
    print("""
Usage: """ + prog + """ <command> [option] <arguments>
    (Use """ + prog + """ <command> --help to display help information for a specific command)

Description:
    This is the TIRA setup main script which parses all the command line inputs
    for administrating TIRA hosts.

    Optional Setup:
        (1) initialize tira tools: ./""" + prog + """ init -i
        (2) install tira autocomplete: """ + prog + """ autocomplete -i

    Steps for setting up a TIRA NFS Server:
        (1) create the nfs server with: """ + prog + """ nfs-create
        (2) create user : """ + prog + """ user -c <NFSHost>
            <NFSHost> should be a tira nfs host (see nfs-create)

    Steps for setting up a TIRA Host:
        (1) create user : """ + prog + """ user -c <NFSHost>
            <NFSHost> should be a tira nfs host (see nfs-create)
        (2) create the host with: """ + prog + """ host-create <NFSHost> <ETH>
            <NFSHost> should be a tira nfs host (see nfs-create)
            <ETH> should be active ethernet port connected to (eg. eth0)
            ...

Options:
    -h | --help       Display help documentation

Commands:
    host-create       Create a TIRA host (needs sudo)
    host-delete       Delete a TIRA host (needs sudo)
    nfs-create        Create a local instance of a NFS server (needs sudo)
    exchange-keys     SSH Key exchange with all registred hosts (or one specific)
    user              Create or delete tira user.
    autocomplete      Installs or removes TIRA autocomplete scripts.
    init              Initialize TIRA tools.
    update            Install new tira version

Authors:

    Steve Göring
    """)


def getcommands():
    """
    Returns all available subscript commands with minimum argument count.
    """
    return {"host-create": 2,
            "host-delete": 0,
            "exchange-keys": 0,
            "nfs-create": 0,
            "user": 1,
            "autocomplete": 1,
            "init": 1,
            "update": 0}


def main(args):
    """
    TIRA setup main script for calling setup sub scripts.
    """
    commands = getcommands()

    TIRA_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
    conf = source(TIRA_SCRIPT_PATH + "/core/config.sh")

    logInfo("tira version: {0}".format(conf["_TIRA_VERSION"]))
    logInfo("tira setup called.")

    logDebug("arguments:" + str(args))

    # Check command line arguments.
    if len(args) == 0:
        logError("Need more parameter, see: ")
        usage()
        return

    # Check if help is needed.
    if args[0] in ["--help", "-h"]:
        logInfo("Help screen:")
        usage()
        return

    if args[0] not in commands:
        logError("Wrong command: ")
        usage()
        return

    command = args[0]

    if "--help" in args[1:] or "-h" in args[1:] or len(args[1:]) < commands[command]:
        logInfo("Call local help screen of subscipt.")
        call = [scriptDir() + "/tira-" + command + ".sh"] + ["-h"]
        # Call help and modify local generated help messag to fit with tira-setup call.
        print(shell_call(call).replace("tira-" + command + ".sh", get_prog_name() + " " + command))
        return


    if os.geteuid() != 0:
        logError("sudo needed for " + get_prog_name() + " try: sudo " + " ".join([get_prog_name()] + args))
        return

    # run command
    params = args[1:]

    call = [scriptDir() + "/tira-" + command + ".sh"] + params
    logDebug("call: " + str(call))
    p = subprocess.Popen(call, shell=False, stdout=sys.stdout, stderr=subprocess.STDOUT)

    retval = p.wait()
    sys.exit(retval)

if __name__ == "__main__":
    main(sys.argv[1:])
