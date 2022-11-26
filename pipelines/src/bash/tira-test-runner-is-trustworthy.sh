#!/bin/sh

echo "Check that the runner is trustworthy..."

URLS="google.com github.com gitlab.com webis.de"

which curl  2> /dev/null 1> /dev/null

if [ "$?" != "0" ]; then
    echo -e " [\033[0;31mx\033[0m] Required tool is not installed. I abort the run"
    exit 1
fi

for URL in ${URLS}
do
    CURL_OUTPUT=$(curl -m 5 -i "${URL}" 2>&1|grep -i "http")
   
    if [ "$?" == "0" ]; then
        echo -e " [\033[0;31mx\033[0m] The runner has access to the internet. I abort the run."
        exit 1
    fi
done

echo -e " [\033[0;32mo\033[0m] The runner has no access to the internet."

echo -e "TODO: check only allowed files are readable"

