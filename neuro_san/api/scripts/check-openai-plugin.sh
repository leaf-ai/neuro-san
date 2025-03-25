#!/bin/bash

set -e

REQUIRED_GO_VERSION="1.23"

# Function to compare Go versions
version_ge() {
  [ "$1" = "$2" ] && return 0
  [ "$(printf "%s\n" "$@" | sort -V | head -n 1)" != "$1" ]
}

echo "🔍 Checking for protoc-gen-openapi in PATH..."

if command -v protoc-gen-openapi >/dev/null 2>&1 && [ -x "$(command -v protoc-gen-openapi)" ]; then
  echo "✅ Found protoc-gen-openapi at: $(command -v protoc-gen-openapi)"
  exit 0
fi

echo "❌ protoc-gen-openapi not found in PATH or not executable."
echo ""
echo "📋 To install it, follow these steps:"

OS=$(uname)

if [[ "$OS" == "Darwin" ]]; then
  echo ""
  echo "🛠 macOS Installation:"
  echo "1. Install Go (version >= $REQUIRED_GO_VERSION):"
  echo "   brew install go"
  echo ""
  echo "2. Install protoc-gen-openapi plug-in:"
  echo "   go install github.com/google/gnostic/cmd/protoc-gen-openapi@latest"
  echo ""
  echo "3. Add to PATH:"
  echo "   export PATH=\"\$PATH:\$HOME/go/bin\""
elif [[ "$OS" == "Linux" ]]; then
  echo ""
  echo "🛠 Linux Installation:"
  echo "1. Install Go (version >= $REQUIRED_GO_VERSION):"
  echo "   Visit https://go.dev/dl/ and download the latest Go tarball"
  echo "   Example:"
  echo "   wget https://go.dev/dl/go1.23.0.linux-amd64.tar.gz"
  echo "   sudo rm -rf /usr/local/go"
  echo "   sudo tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz"
  echo "   export PATH=\"\$PATH:/usr/local/go/bin\""
  echo ""
  echo "2. Install protoc-gen-openapi plug-in:"
  echo "   go install github.com/google/gnostic/cmd/protoc-gen-openapi@latest"
  echo ""
  echo "3. Add to PATH:"
  echo "   export PATH=\"\$PATH:\$HOME/go/bin\""
else
  echo "⚠️ Unsupported OS: $OS"
fi

exit 1
