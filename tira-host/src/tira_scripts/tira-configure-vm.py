#!/usr/bin/env python2
# -*- coding: utf8 -*-
"""
    Copyright 2014-today www.webis.de
    Project TIRA

    Author: Anna Beyer, Adrian Teschendorf, Steve Göring, Martin Potthast
"""

import sys
import os
import string
import random
import socket
import datetime
import subprocess
import pickle

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/core/")

from pythoncore import *

TIRA_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
SCRIPT_GENERIC = TIRA_SCRIPT_PATH + "/tira-configure-vm.sh"
SCRIPT_WINDOWS = TIRA_SCRIPT_PATH + "/tira-configure-vm-windows.sh"
SCRIPT_UBUNTU = TIRA_SCRIPT_PATH + "/tira-configure-vm-ubuntu.sh"
SCRIPT_FEDORA = TIRA_SCRIPT_PATH + "/tira-configure-vm-fedora.sh"
SCRIPT_ALPINE = TIRA_SCRIPT_PATH + "/tira-configure-vm-alpine.sh"

DEFAULT_PORT_SSH = 44400
DEFAULT_PORT_RDP = 55500

# Read bash-config file.
conf = source(TIRA_SCRIPT_PATH + "/core/config.sh")

VMS_TXT = conf["_CONFIG_FILE_tira_vms"]
VMLOG_TXT = conf["_CONFIG_FILE_tira_vms_log"]
VM_OVERVIEW = conf["_CONFIG_FILE_tira_local_home"] + "/vms.txt"

USERS_TXT = conf["_CONFIG_FILE_tira_users_txt"]
VIRTUAL_MACHINES_DIR = conf["_CONFIG_FILE_tira_model_virtual_machines_dir"]

VM_OVERVIEW_HEADER = "host-pc vmname=vmid-os tiraport sshport rdpport " \
    "admin admin-pw user user-pw"
SEPARATOR = "-" * 79

CHAR_SET = string.ascii_lowercase + string.digits + string.ascii_uppercase


def usage():
    """ Define and print usage Screen. """
    print "\nusage:", get_prog_name(), "OVA USER"
    print """
    Script to instantiate, configure and start a new vm instance from OVA and
    add a user account for USER.
    OVA       Is a VirtualBox appliance file.
    USER      The user name of the participant.

    Authors:
        Anna Beyer
        Adrian Teschendorf
        Steve Göring
    """


def assign_id():
    """ Assign ID to vm. """
    vmid = 1
    if os.path.isfile(VM_OVERVIEW):
        vms = [x.rstrip() for x in file(VM_OVERVIEW).readlines() if x.rstrip() != SEPARATOR]
        vms.pop(0)  # remove header

        vm_ids = set()
        for vm in vms:
            host_pc, vm_name, vm_ip, vm_sshport, vm_rdpport, \
                admin_name, admin_pw, user_name, user_pw, = vm.split(' ')

            vm_id = int(vm_sshport) - DEFAULT_PORT_SSH
            vm_ids.add(int(vm_id))
        overview = open(VM_OVERVIEW, 'r')
        if len(vm_ids) > 0:
            allowed_ids = set(range(1, 51)) # TODO: Lift the limit of 50 VMs per machine.
            missing_ids = sorted(list(allowed_ids - set(vm_ids)))
            if len(missing_ids) > 0:
               vmid = missing_ids[0]
            else:
               return 51
    else:
        overview = open(VM_OVERVIEW, 'w')
        header = VM_OVERVIEW_HEADER + '\n'
        overview.write(header)
        overview.flush()
    overview.close()
    return vmid

def generate_random_string():
    """
    Generate random string with 8 characters of digits,
    lowercase and uppercase letters.
    """
    return ''.join(random.sample(CHAR_SET, 8))


def get_host_name():
    """ Get host name. """
    # Get host name: webisXY
    name = socket.gethostname()
    name = name if 'medien' in name else name + ".medien.uni-weimar.de"
    return name


def get_host_id():
    """ Get host id. """
    # Get host name: webisXY
    # Should return 0 on all new machines (e.g. betaweb). Non-Null on old webis-machines
    import re
    name = socket.gethostname()
    number = re.findall(r'[1-9][0-9]*$', name)
    if 'betaweb' not in name.lower() and len(number) > 0:
        return number[0]
    else:
        return "0"


def main(args):
    """ Main function."""

    # Get arguments.
    ova = args[0]
    user = args[1]

    # Assign id.
    vmid = assign_id()

    # Get host name.
    host = os.environ.get('TIRA_FQDN', get_host_name())

    # Generate vm-name.
    if '/' in ova:
        vmname = user + "-" + "%02d" % vmid + "-" + ova[ova.rindex('/') + 1:-4]
    else:
        vmname = user + "-" + "%02d" % vmid + "-" + ova[:-4]

    if len(vmname) > 64:
        print "\n\nVM Name exceeds 64 characters! Please choose a shorter name and rerun the command"
        sys.exit(0)

    # Set ports.
    sshport = DEFAULT_PORT_SSH + vmid
    rdpport = DEFAULT_PORT_RDP + vmid

    # Set ip adress.
    ip = "10." + get_host_id() + "." + str(vmid) + ".1"

    # Generate admin password.
    admin = "administrator"
    adminpw = generate_random_string()

    # Generate user password.
    userpw = generate_random_string()

    # Execute generic configuration script
    command = "bash %s %s %s %s %s %s %d %d %s\n" % (SCRIPT_GENERIC, ova, vmname, user, userpw, ip, sshport, rdpport, adminpw)
    os.system(command)

    # Generate shell script call based on used operating system.
    if "windows" in ova:
        shellscript = SCRIPT_WINDOWS
    elif "ubuntu" in ova:
        shellscript = SCRIPT_UBUNTU
    elif "fedora" in ova:
        shellscript = SCRIPT_FEDORA
    elif "alpine" in ova:
        shellscript = SCRIPT_ALPINE

    command = "bash %s %s %s %s %s\n" % (shellscript, user, userpw, ip, adminpw)
    os.system(command)

    # Generate overview line.
    line = "%s %s %s %d %d %s %s %s %s\n" % (host, vmname, ip, sshport, rdpport, admin, adminpw, user, userpw)

    # Write output to file.
    overview = open(VM_OVERVIEW, 'a')
    overview.write(line)
    overview.close()

    # Write line to VMS_TXT.
    # Format: host\t vm-name \n
    vmstxt = open(VMS_TXT, 'a')
    vmstxt.write(socket.gethostname() + "\t" + vmname + "\n")
    vmstxt.close()

    # Write line to VMLOG_TXT.
    # Format: host vm-name date created
    vmlogtxt = open(VMLOG_TXT, 'a')
    timestamp = datetime.datetime.now()
    vmlogtxt.write(socket.gethostname() + " " + vmname + " " + timestamp.strftime("%Y-%m-%d") + " created\n")
    vmlogtxt.close()

    # Print overview.
    user_entry = {
        "host": host,
        "vmId": vmid,
        "vmName": vmname,
        "userName": user,
        "virtualMachineId": user,
        "userPw": userpw,
        "adminName": admin,
        "adminPw": adminpw,
        "ip": ip + "00",
        "portSsh": sshport,
        "portRdp": rdpport
    }
    print("entry for users.prototext:\n")

    user_entry_str = ""
    user_entry_str = "users {\n"

    for key in user_entry:
        user_entry_str += """  {0}: "{1}" """.format(key, user_entry[key]) + "\n"
    user_entry_str += "}\n"
    print(user_entry_str)

    f = open(USERS_TXT, "a")
    f.write(user_entry_str)
    f.close()

    f = open(VIRTUAL_MACHINES_DIR + "/" + user + ".prototext", "w")
    for key in user_entry:
        f.write("""  {0}: "{1}" """.format(key, user_entry[key]) + "\n")
    f.close()

    print "\n\nTEST RDP"
    print "rdesktop %s:%d -u %s -p %s" % (host, rdpport, user, userpw)
    print "\nTEST SSH"
    print("sshpass -p %s ssh %s@%s -p %d -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" % (userpw, user, host, sshport))
    print ""

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage()
        sys.exit(1)
    main(sys.argv[1:])

