#!/bin/sh
# Generates a tinyproxy configuration that only allows access to the hostnames listed (as a
# comma-separated list) in the TIRA_ALLOWED_HOSTNAMES environment variable, then starts tinyproxy.
set -eu

: "${TIRA_ALLOWED_HOSTNAMES:?TIRA_ALLOWED_HOSTNAMES must be set to a comma-separated list of hostnames}"

CONF_FILE=/etc/tinyproxy/tinyproxy.conf
FILTER_FILE=/etc/tinyproxy/filter

mkdir -p /etc/tinyproxy /var/run/tinyproxy

: > "$FILTER_FILE"
IFS=','
for hostname in $TIRA_ALLOWED_HOSTNAMES; do
    hostname=$(echo "$hostname" | xargs)
    [ -z "$hostname" ] && continue
    # Anchor the pattern so that, e.g., "example.com" does not also match "evil-example.com".
    echo "^${hostname}$" >>"$FILTER_FILE"
done
unset IFS

cat >"$CONF_FILE" <<EOF
User tinyproxy
Group tinyproxy
Port 8888
Listen 0.0.0.0
Timeout 600
MaxClients 100
LogLevel Info
PidFile "/var/run/tinyproxy/tinyproxy.pid"

# Whitelist: only requests to hostnames matching the patterns in \$FILTER_FILE are allowed, all other
# destinations are denied.
Filter "$FILTER_FILE"
FilterDefaultDeny Yes
FilterExtended Yes
EOF

echo "Allowing network access to the following hostnames: $TIRA_ALLOWED_HOSTNAMES"

exec tinyproxy -d -c "$CONF_FILE"
