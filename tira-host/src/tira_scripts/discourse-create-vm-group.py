#!/usr/bin/env python2
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/core/")

TIRA_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
SCRIPT_DISCOURSE = TIRA_SCRIPT_PATH + "/discourse-create-vm-group.sh"


def discourse_invite_link(user):
    cmd = [SCRIPT_DISCOURSE, user]
    try:
        ret = subprocess.check_output(cmd)
        return ret.split('\n')[-2]
    except:
        return 'Error during the creation of the discourse invite-link. Please run "' + (' '.join(cmd)) + '".'

if __name__ == "__main__":
    user_name = sys.argv[-1]
    invite_link = discourse_invite_link(user_name)

    print "\nDiscourse Invite"
    print invite_link
    print "\nDiscourse Invite Mail"
    print "Please use this link to create your login for TIRA: " + invite_link + ". After login to TIRA, you can find the credentials and usage examples for your dedicated virtual machine " + user_name + " here: https://www.tira.io/g/tira_vm_" + user_name
    print ""

