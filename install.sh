#!/bin/bash
set -e

echo "========================================="
echo "  Secret Server Installation (Termux)"
echo "========================================="
echo ""

# Detect if running in Termux
if [ ! -d "$PREFIX" ]; then
    echo "⚠️  Warning: This script is designed for Termux on Android."
    echo "   It may not work correctly on other systems."
    echo ""
fi

# 1. Update packages
echo "📦 Step 1/5: Updating packages..."
pkg update -y && pkg upgrade -y

# 2. Install dependencies
echo "🔧 Step 2/5: Installing dependencies (Python, GPG, Git, and build tools)..."
# Install build deps required for compiling some Python packages (e.g., cryptography)
pkg install -y python gnupg git clang rust openssl-dev libffi-dev


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
