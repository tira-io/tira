#!/usr/bin/env python2
# -*- coding: utf8 -*-
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Steve Göring
"""
import sys
import os


def getcommands():
    """
    Returns all available subscript commands with minimum argument count.
    """
    return {"k8s": 1,
            "host-list": 0,
            "exchange-keys": 0,
            "run-copy-to-local": 7,
            "run-execute": 4,  # - 5
            "run-eval": 4,
            "start": 0,
            "status": 0,
            "stop": 0,
            "backup": 1,
            "import": 1,
            "vm-backup": 2,
            "vm-import": 1,
            "vm-create": 1,
            "vm-delete": 1,
            "vm-info": 1,  # - 2..
            "vm-info-backup": 1,
            "vm-list": 0,  # - 2..
            "vm-metrics": 1,
            "vm-modify": 3,
            "vm-restore": 2,
            "vm-runtime-output": 2,
            "vm-sandbox": 3,
            "vm-screenshot": 1,
            "vm-shutdown": 1,
            "vm-snapshot": 2,
            "vm-start": 1,
            "vm-stop": 1,
            "vm-unsandbox": 1,
            "vm-ssh": 1,
            "vm-rdp": 1,
            "test": 0}


def main(args):
    """
    Python helper script for parsing tira command line arguments.
    """
    print("# arguments = " + str(args))

    if len(args) == 0 or args[0] == '':
        print("no_arguments=true")
        sys.exit(0)

    if args[0] in ["-h", "--help"]:
        print("help=true")
        sys.exit(0)

    # Aviable commands, command : min argument count.
    commands = getcommands()

    if args[0] not in commands:
        print("error='option does not exist!'")
        sys.exit(0)

    script = args.pop(0)
    cmd = script.replace("-", "_")

    print("# script args=" + str(args))

    # Extract remote & host, "-r HOST" can be everywhere. (do not manipulate the passed args for the k8s script)
    if len(args) != 0 and ("-r" in args or "--remote" in args) and not 'k8s' in script:
        if "-r" in args:
            pos = args.index("-r")
        else:
            pos = args.index("--remote")

        args.pop(pos)
        print("# " + str(args))
        print("# " + str(pos))
        if pos >= len(args):
            print("error='remote host needed'")
            sys.exit(0)

        host = args.pop(pos)
        if host == "":  # default case, if something is wrong with host
            host = "localhost"
        print("host='" + str(host) + "'")
        print("remote=true")

    print("cmd='" + str(cmd) + "'")
    print("script='" + str(script) + "'")
    print("args='" + str(" ".join(args)) + "'")
    print("minarg_count=" + str(commands[script]))

    if commands[script] <= len(args):
        print("has_minarg_count=true")

    if "-h" in args or "--help" in args:
        print("local_help=true")


if __name__ == "__main__":
    main(sys.argv[1:])
