#!/bin/bash
#
#    Project bash code style checker
#    Copyright 2015
#
#    Code style and bash/python correctnes check tool
#
#    Author: Steve Göring
#
PATH="./codestyle/:$PATH"

# Include config file.
. config.sh

#
#    Printout error to stderr.
#
logError() {
    echo -e "\033[91m[ERROR]\033[0m $@ " 1>&2;
}

#
#    Printout info message.
#
logInfo() {
    echo -e "\033[92m[INFO ]\033[0m $@"
}

#
#    Checks if needed tools are available.
#
#    \params $@ list of tools
#    Example call:
#        checktools "bash nano"
#
check_tools() {
    for tool in $@; do
        which $tool > /dev/null

        if [[ "$?" -ne 0 ]]; then
            logError "$tool is not installed."
            exit 1
        fi
    done
    logDebug "Each needed tool ($@) is installed."
}

# First check if needed tools are available.
check_tools codeconventions shellcheck checkbashisms pep8

#
#   Usage screen.
#
usage() {
    logInfo "checks every '*.sh' and '*.py' in '$_SRC_DIR' directory"
    exit 1
}

#
#    Perform code style check of all used python scripts.
#
#    \params $1 input path
#
check_python_scripts() {
    logInfo "check python scripts"
    checkpath="$1"
    allFiles=$(ls -1Sr $checkpath | wc -l)
    logInfo "apply pep8 for $allFiles files"

    # Handle each python file in src, ascending sorted by size.
    c=0
    for i in $(ls -1Sr $checkpath); do
        logInfo "check $i"

        pep8 --ignore=E501 "$i"
        if [ "$?" -ne 0 ]; then
            logError "fix $i   ($c/$allFiles)"
            return
        fi
        c=$((c + 1))
    done
}

#
#    Perform code style check of all used bash scripts.
#
#    \params $1 input path
#
check_bash_scripts() {
    logInfo "check bash scripts"
    checkpath="$1"
    allFiles=$(ls -1Sr $checkpath | wc -l)
    logInfo "apply codeconventions, checkbashisms and shellcheck for $allFiles files"

    # Handle each bash file in path, ascending sorted by size.
    c=0
    for i in $(ls -1Sr $checkpath); do
        logInfo "check $i"

        codeconventions "$i" && checkbashisms -f "$i" && shellcheck -e SC2029,SC2145,SC2086 "$i"
        if [ "$?" -ne 0 ]; then
            logError "fix $i   ($c/$allFiles)"
            return
        fi
        c=$((c + 1))
    done
}

#
#    Printout code statistics.
#
#    \params $1 input path
#
print_code_info() {
    logInfo "Code statistics"
    checkpath="$1"

    echo "" > "tmp_wc"
    for i in $(find "$checkpath" -name "*.py" -o -name "*.sh" | grep -v libs)
    do
        cat "$i" >> "tmp_wc"
    done
    linesOfCode=$(wc -l "tmp_wc")
    logInfo "lines of code: $linesOfCode"
    rm "tmp_wc"
}


#
#   Codechecker main.
#
main() {
    if [ "$1" = "-h" ]; then
        usage
    fi

    if [ "$1" = "-py" ]; then
        check_python_scripts "$_SRC_DIR/*.py"
        exit 0
    fi

    if [ "$1" = "-sh" ]; then
        check_bash_scripts "$_SRC_DIR/*.sh"
        exit 0
    fi

    check_python_scripts "$_SRC_DIR/*.py"
    check_bash_scripts "$_SRC_DIR/*.sh"

    # printout codestatistics
    print_code_info "$_SRC_DIR"
}

main "$@"