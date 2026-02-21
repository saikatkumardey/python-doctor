#!/bin/sh
set -e

REPO="saikatkumardey/python-doctor"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
BINARY_NAME="python-doctor"

detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux";;
        Darwin*) echo "macos";;
        MINGW*|MSYS*|CYGWIN*) echo "win";;
        *) echo "unsupported";;
    esac
}

detect_arch() {
    case "$(uname -m)" in
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
        VERSION=$(curl -sL "https://api.github.com/repos/${REPO}/releases/latest" | grep -o '"tag_name": *"v[^"]*"' | sed 's/.*"v//;s/".*//')
    fi
    echo "$VERSION"
}

download() {
    os=$(detect_os)
    arch=$(detect_arch)
    ext=$(get_extension)
    v=$(version)
    url="https://github.com/${REPO}/releases/download/v${v}/${BINARY_NAME}-${os}${ext}"

    echo "Downloading python-doctor v${v} for ${os}-${arch}..."
    curl -fSL "$url" -o "${INSTALL_DIR}/${BINARY_NAME}${ext}"
    chmod +x "${INSTALL_DIR}/${BINARY_NAME}${ext}"
}

install() {
    mkdir -p "$INSTALL_DIR"
    download
    echo "Installed to ${INSTALL_DIR}/${BINARY_NAME}$(get_extension)"
    echo "Make sure ${INSTALL_DIR} is in your PATH"
}

install
