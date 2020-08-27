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
#    Install tira auto completion script.
#
install_auto_script() {
    logInfo "Install autocomplete script. sudo needed."
    autocomplete_script="$scriptPath/core/tira"
    if [ ! -d "/etc/bash_completion.d" ]; then
        logError "There is no bash_completion.d directory in /etc/, please install bash_completion."
        exit 1
    fi
    sudo cp "$autocomplete_script" "/etc/bash_completion.d/tira" >/dev/null
}

#
#    Remove tira auto completion script.
#
remove_auto_script() {
    logInfo "Remove autocomplete script. sudo needed."
    autocomplete_script="$scriptPath/core/tira"
    if [ ! -d "/etc/bash_completion.d" ]; then
        logError "There is no bash_completion.d directory in /etc/, please install bash_completion."
        exit 1
    fi
    if [ ! -f "/etc/bash_completion.d/tira" ]; then
        logError "Tira autocomplete was not installed, exit."
        exit 1
    fi
    sudo rm -rf "/etc/bash_completion.d/tira"
}

#
#    Define command line arguments and parse them.
#
DEFINE_boolean install false 'install tira auto complete scripts' 'i'
DEFINE_boolean remove false 'remove tira auto complete scripts' 'r'

FLAGS_HELP=$(usage)
export FLAGS_HELP
FLAGS "$@" || exit 1  # Parse command line arguments.
eval set -- "${FLAGS_ARGV}"

#
#    Creates or deletes tira user with all settings.
#
main() {

    install="${FLAGS_install}"
    remove="${FLAGS_remove}"

    if [ "$install" = "${FLAGS_TRUE}" ] && [ "$remove" = "${FLAGS_TRUE}" ]; then
        logError "Parameters install and remove cannot be combined, see:"
        usage
    fi

    # Create or delete tira user.
    if [ "$install"  = "${FLAGS_TRUE}" ]; then
        install_auto_script
        return
    fi
    if [ "$remove" = "${FLAGS_TRUE}" ]; then
        remove_auto_script
        return
    fi

    logError "Parameter needed, see:"
    usage
}

#
#    Start programm with parameters.
#
main "$@"
