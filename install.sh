#!/bin/sh
set -e

REPO="saikatkumardey/python-doctor"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
BINARY_NAME="python-doctor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux";;
        Darwin*) echo "macos";;
        MINGW*|MSYS*|CYGWIN*) echo "win";;
        *) echo "unsupported";;
    esac
}

detect_arch() {
    arch=$(uname -m)
    case "$arch" in
        x86_64|AMD64) echo "x86_64";;
        aarch64|arm64) echo "arm64";;
        *) echo "x86_64";;
    esac
}

get_extension() {
    case "$(detect_os)" in
        win) echo ".exe";;
        *)   echo "";;
    esac
}

version() {
    if [ -z "$VERSION" ]; then
        # Fetch latest tag name (e.g., v2026.2.22)
        LATEST_TAG=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" | grep -o '"tag_name": *"[^"]*"' | head -n 1 | sed 's/.*"\(.*\)".*/\1/')
        if [ -z "$LATEST_TAG" ]; then
            echo "Error: Could not determine latest version." >&2
            exit 1
        fi
        VERSION="$LATEST_TAG"
    fi
    echo "$VERSION"
}

download() {
    os=$(detect_os)
    arch=$(detect_arch)
    ext=$(get_extension)
    v=$(version)
    
    # Map detection to release binary names
    # matrix.artifact_name from release.yml:
    # python-doctor-linux-x86_64
    # python-doctor-macos-arm64
    # python-doctor-macos-x86_64
    # python-doctor-win-x86_64
    
    asset_name="${BINARY_NAME}-${os}-${arch}${ext}"
    url="https://github.com/${REPO}/releases/download/${v}/${asset_name}"

    printf "${GREEN}Downloading ${BINARY_NAME} ${v} for ${os}-${arch}...${NC}\n"
    
    if ! curl -fSL "$url" -o "${INSTALL_DIR}/${BINARY_NAME}${ext}"; then
        printf "${RED}Error: Failed to download binary from ${url}${NC}\n"
        printf "This version might not have a binary for your architecture yet.\n"
        exit 1
    fi
    
    chmod +x "${INSTALL_DIR}/${BINARY_NAME}${ext}"
}

install() {
    if [ "$(detect_os)" = "unsupported" ]; then
        printf "${RED}Error: Unsupported operating system: $(uname -s)${NC}\n"
        exit 1
    fi

    mkdir -p "$INSTALL_DIR"
    download
    
    printf "${GREEN}Successfully installed to ${INSTALL_DIR}/${BINARY_NAME}$(get_extension)${NC}\n"
    
    # Check if INSTALL_DIR is in PATH
    case ":$PATH:" in
        *":${INSTALL_DIR}:"*) ;;
        *) printf "\n${RED}Warning: ${INSTALL_DIR} is not in your PATH.${NC}\n"
           printf "Add it to your shell config (e.g., ~/.bashrc or ~/.zshrc):\n"
           printf "  export PATH=\"\$PATH:${INSTALL_DIR}\"\n"
           ;;
    esac
}

install
