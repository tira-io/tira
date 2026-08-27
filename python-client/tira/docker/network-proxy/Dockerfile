# docker build -t ghcr.io/tira-io/tira-proxy:0.0.1 .
# A minimal HTTP(S) forward proxy that only allows CONNECT/requests to an explicit allowlist of
# hostnames (passed via the TIRA_ALLOWED_HOSTNAMES environment variable as a comma-separated list).
#
# Used by tira.network_proxy to give a sandboxed execution access to only a small, configurable set of
# external services instead of unrestricted network access.
FROM alpine:3.20

RUN apk add --no-cache tinyproxy

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8888

ENTRYPOINT ["/entrypoint.sh"]
