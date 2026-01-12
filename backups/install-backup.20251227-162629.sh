#!/bin/bash
set -e

echo "========================================="
echo "  Secret Server Installation (Termux)"
echo "========================================="
echo ""

# Termux-only installer
# Use a stricter Termux detection: require the 'pkg' command and a Termux $PREFIX path.
if ! command -v pkg >/dev/null 2>&1 || [ -z "$PREFIX" ] || [[ "$PREFIX" != /data/data/com.termux* ]]; then
    echo "⚠️  This installer is for Termux on Android only. Aborting."
    echo "   If you need a different installer, see README.md or run manual setup steps."
    echo ""
    exit 1
fi

# 1. Update packages
echo "📦 Step 1/5: Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Install dependencies
echo "🔧 Step 2/5: Installing dependencies (Python, Git, and build tools)..."
# Install the minimal required packages for running and building dependencies (e.g., cryptography).
# Optional tools for convenience: 'curl' and 'gnupg'.
# NOTE: Termux package names (no '-dev' suffixes).

# Helper: check for presence of a header or pkg-config entry
check_header() {
    local hdr="$1" pkgname="$2"
    if command -v pkg-config >/dev/null 2>&1 && pkg-config --exists "$pkgname" 2>/dev/null; then
        return 0
    fi
    # Check common include paths: Termux $PREFIX and system /usr/include
    if [ -n "$PREFIX" ] && [ -f "$PREFIX/include/$hdr" ]; then
        return 0
    fi
    if [ -f "/usr/include/$hdr" ]; then
        return 0
    fi
    return 1
}

# Map logical dependency to Termux package name
# Note: termux packages: openssl, libffi, python, git, clang, rust
REQ_PKGS=(python git clang rust openssl libffi)

MISSING=()
# Check binaries first
if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    MISSING+=(python)
fi
if ! command -v git >/dev/null 2>&1; then
    MISSING+=(git)
fi
if ! command -v clang >/dev/null 2>&1; then
    MISSING+=(clang)
fi
if ! command -v rustc >/dev/null 2>&1 && ! command -v cargo >/dev/null 2>&1; then
    MISSING+=(rust)
fi
# Check headers for openssl and libffi
if ! check_header "openssl/ssl.h" "libssl"; then
    MISSING+=(openssl)
fi
if ! check_header "ffi.h" "libffi"; then
    MISSING+=(libffi)
fi

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "Installing missing packages: ${MISSING[*]}"
    FAILED_PACKAGES=()
    for pkgname in "${MISSING[@]}"; do
        echo "-> Installing: $pkgname"
        PKG_LOG=$(mktemp /tmp/secret_server_pkg.${pkgname}.XXXXXX)
        if ! pkg install -y "$pkgname" 2>&1 | tee "$PKG_LOG"; then
            echo "\nError: package '$pkgname' failed to install. Showing the tail of the output:"
            echo "---- $PKG_LOG (last 200 lines) ----"
            tail -n 200 "$PKG_LOG" || true
            echo "---- end of $PKG_LOG ----"
            FAILED_PACKAGES+=("$pkgname")
        else
            echo "Package '$pkgname' installed successfully."
            rm -f "$PKG_LOG"
        fi
    done

    if [ ${#FAILED_PACKAGES[@]} -gt 0 ]; then
        echo "\nThe following packages failed to install: ${FAILED_PACKAGES[*]}"
        echo "You can try installing them manually, e.g.:"
        echo "  pkg install -y ${FAILED_PACKAGES[*]}"
        echo "The installer will continue to clone the repo, but Python package builds (e.g., 'cryptography') may fail if system headers are missing."
    fi
else
    echo "All required packages appear to be present."
fi

# Verify headers are available now
if ! check_header "openssl/ssl.h" "libssl"; then
    echo "\nError: OpenSSL development headers still not found (openssl/ssl.h)."
    echo "On Termux:  pkg install openssl"
    echo "If the issue persists, ensure your distribution provides OpenSSL development headers."
    exit 1
fi
if ! check_header "ffi.h" "libffi"; then
    echo "\nError: libffi headers not found (ffi.h)."
    echo "On Termux:  pkg install libffi"
    echo "If the issue persists, ensure your distribution provides libffi development headers."
    exit 1
fi


# 3. Clone or update repository
INSTALL_DIR="$HOME/secret-server"
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Step 3/5: Repository already exists, updating..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📂 Step 3/5: Cloning repository..."
    cd "$HOME"
    git clone https://github.com/JohnBlakesDad/secret-server.git
    cd "$INSTALL_DIR"
fi

# 4. Install Python requirements
echo "🐍 Step 4/5: Installing Python libraries into a virtualenv..."
# Create a venv named 'venv' and install requirements inside it
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# Deactivate to avoid leaving venv active in the installer
deactivate || true

# 5. Create command alias
echo "🔗 Step 5/5: Creating 'secret-server' command..."
mkdir -p "$HOME/.termux"
BASHRC="$HOME/.bashrc"

# Add alias if not already present
if ! grep -q "alias secret-server=" "$BASHRC" 2>/dev/null; then
    echo "alias secret-server='cd $INSTALL_DIR && ./start_server.sh'" >> "$BASHRC"
    echo "✅ Added 'secret-server' command to .bashrc"
else
    echo "✅ 'secret-server' command already configured"
fi

# Setup boot script (optional)
echo ""
echo "📱 Optional: Auto-start on boot"
echo "   To make Secret Server start automatically:"
echo "   1. Install 'Termux:Boot' from F-Droid"
echo "   2. Open Termux:Boot once to register it"
echo "   3. Run: mkdir -p ~/.termux/boot && cp $INSTALL_DIR/termux_boot.sh ~/.termux/boot/"
echo ""

echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "To start Secret Server:"
echo "  1. Close and reopen Termux (to load new commands)"
echo "  2. Type: secret-server"
echo "  3. Open browser to: http://localhost:5001"
echo ""
echo "Installation directory: $INSTALL_DIR"
echo ""
