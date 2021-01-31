#!/usr/bin/env python2

def discourse_invite_link(user):
    cmd = [SCRIPT_DISCOURSE, user]
    try:
        import subprocess
        ret = subprocess.check_output(cmd)
        return ret.split('\n')[-1]
    except:
        return 'Error during the creation of the discourse invite-link. Please run "' + (' '.join(cmd)) + '".'

if __name__ == "__main__":
    import sys
    user_name = sys.argv[-1]
    invite_link = discourse_invite_link(user_name)

    print "\nDiscourse Invite"
    print invite_link
    print "\nDiscourse Invite Mail"
    print "Please use this link to create your login for TIRA: " + invite_link + ". After login to TIRA, you can find the credentials and usage examples for your dedicated virtual machine " + user_name + " here: https://www.tira.io/g/tira_vm_" + user_name
    print ""

