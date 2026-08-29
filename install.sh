#!/bin/bash
# Backwards-compatible wrapper — the setup now lives in the `macsetup` CLI.
#   ./macsetup status   show drift
#   ./macsetup apply    converge
#   ./macsetup doctor   conflicts + advisories
#   ./macsetup test -i  interactive verification
exec "$(cd "$(dirname "$0")" && pwd)/macsetup" apply "$@"
