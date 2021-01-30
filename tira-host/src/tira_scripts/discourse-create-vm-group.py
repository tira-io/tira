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
    print "\nDiscourse Invite"
    print discourse_invite_link(sys.argv[-1])
    print ""

