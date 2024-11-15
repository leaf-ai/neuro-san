#!/usr/bin/env bash

#
# This script runs "shellcheck" on all¹ the shell scripts found in the current and subdirectories of the project.
# If any issues are found, the exit code is non-zero (typically, 123 from empirical observation of shellcheck).
# Thus any build stages that run this script will fail if any issues are found.
#
# ¹ Scripts within directories that match the names in EXCLUDE_DIRS will not be included.

# See https://www.gnu.org/software/bash/manual/html_node/The-Set-Builtin.html for what these do
set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

# These will be excluded if they appear *anywhere* in the path to the shell script
EXCLUDE_DIRS="leaf-common"

# Find all shell files recursively from current dir. Exclude any that match the EXCLUDE_DIRS.
# Run shellcheck on what remains.
find . -type f -iname "*.sh" | \
  grep -vFwf <(tr " " "\n" <<< "$EXCLUDE_DIRS") | \
  xargs shellcheck
