#!/bin/bash
#
#    Copyright 2014-today www.webis.de
#
#    Project TIRA
#    Author: Steve Göring

#
#    Load libaries and toolkits.
#
scriptPath=${0%/*}
_BASHHELPER="included"
. "$scriptPath"/core/bashhelper.sh
. "$scriptPath"/libs/shflags

#
#    Define and check needed tools for this script.
#
neededtools="cp"
debug && check_tools "$neededtools"  # If debug, check that tools are available.

#
#    Define usage screen.
#
usage() {
    echo "
Usage:
    $(basename "$0") [flags]

Description:

Examples:
    $(basename "$0")

Authors:
    Steve Göring"
    exit 1
}

#
#    Remove tira scripts.
#
remove_tira_scripts() {
    logInfo "Remove tira scripts. sudo needed."

    if [ -L "/usr/bin/tira" ]; then
        sudo unlink "/usr/bin/tira"
    fi

    if [ -L "/usr/bin/tira-setup" ]; then
        sudo unlink "/usr/bin/tira-setup"
    fi
}

#
#    Install tira scripts.
#
install_tira_scripts() {
    logInfo "Install tira scripts. sudo needed."
    scriptpath="$(dirname "$(readlink -f "$0")")"

    # Check if tira links are already there.
    remove_tira_scripts > /dev/null

    sudo ln -s "$scriptpath/tira.sh" "/usr/bin/tira"
    sudo ln -s "$scriptpath/tira-setup.py" "/usr/bin/tira-setup"

}


#
#    Define command line arguments and parse them.
#
DEFINE_boolean install false 'install tira scripts' 'i'
DEFINE_boolean remove false 'remove tira scripts' 'r'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Creates or deletes tira user with all settings.
#
main() {

    install=${FLAGS_install}
    remove=${FLAGS_remove}
    if [ "$scriptPath" != "/usr/lib/tira" ]; then
        logWarn "Be carefully, tira-scripts should be stored in /usr/lib/tira and not in $scriptpath."
    fi

    if [ "$install" = "${FLAGS_TRUE}" ] && [ "$remove" = "${FLAGS_TRUE}" ]; then
        logError "Parameters install and remove cannot be combined, see:"
        usage
    fi

    # Create or delete tira user.
    if [ "$install"  = "${FLAGS_TRUE}" ]; then
        install_tira_scripts
        return
    fi
    if [ "$remove" = "${FLAGS_TRUE}" ]; then
        remove_tira_scripts
        return
    fi

    logError "Parameter needed, see:"
    usage
}

#
#    Start programm with parameters.
#
main "$@"
