#!/bin/bash
#
#    Copyright 2015-today www.webis.de
#
#    Author: Steve Göring
#

#
#    General config file for codechecker
#
_SRC_DIR="../src"


main() {
    export _SRC_DIR
}
#
#    Start programm with parameters.
#
main "$@"