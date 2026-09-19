#!/bin/bash

set -e

# ------------------------------------------------------------
# DDC Monitor Installation Script
# ------------------------------------------------------------

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INSTALL_UI_DIR="/usr/share/ddc-monitor/ui"
INSTALL_DAEMON_DIR="/usr/lib/ddc-monitor"

DBUS_POLICY_DIR="/etc/dbus-1/system.d"
DBUS_SERVICE_DIR="/usr/share/dbus-1/system-services"

SYSTEMD_DIR="/etc/systemd/system"
APPLICATION_DIR="/usr/share/applications"

echo
echo "=========================================="
echo "        DDC Monitor Installation"
echo "=========================================="
echo

# ------------------------------------------------------------
# Check root
# ------------------------------------------------------------

if [ "$EUID" -ne 0 ]; then
    echo "Please run this script with sudo:"
    echo
    echo "    sudo ./install.sh"
    echo
    exit 1
fi

# ------------------------------------------------------------
# Check project files
# ------------------------------------------------------------

echo "[1/8] Checking project files..."

required_files=(
    "$PROJECT_DIR/daemon/ddcutil.py"
    "$PROJECT_DIR/daemon/service.py"

    "$PROJECT_DIR/dbus/org.example.DDCMonitor.conf"
    "$PROJECT_DIR/dbus/org.example.DDCMonitor.service"

    "$PROJECT_DIR/ui/main.py"
    "$PROJECT_DIR/ui/model.py"
    "$PROJECT_DIR/ui/view.py"
    "$PROJECT_DIR/ui/controller.py"
)

for file in "${required_files[@]}"; do

    if [ ! -f "$file" ]; then
        echo "ERROR: Missing file:"
        echo "       $file"
        exit 1
    fi

done

echo "      All required files found."

# ------------------------------------------------------------
# Create directories
# ------------------------------------------------------------

echo "[2/8] Creating installation directories..."

mkdir -p "$INSTALL_UI_DIR"
mkdir -p "$INSTALL_DAEMON_DIR"
mkdir -p "$DBUS_POLICY_DIR"
mkdir -p "$DBUS_SERVICE_DIR"
mkdir -p "$APPLICATION_DIR"

# ------------------------------------------------------------
# Install daemon
# ------------------------------------------------------------

echo "[3/8] Installing daemon..."

install -Dm644 \
    "$PROJECT_DIR/daemon/ddcutil.py" \
    "$INSTALL_DAEMON_DIR/ddcutil.py"

install -Dm755 \
    "$PROJECT_DIR/daemon/service.py" \
    "$INSTALL_DAEMON_DIR/service.py"

# ------------------------------------------------------------
# Install UI
# ------------------------------------------------------------

echo "[4/8] Installing UI..."

install -Dm644 \
    "$PROJECT_DIR/ui/main.py" \
    "$INSTALL_UI_DIR/main.py"

install -Dm644 \
    "$PROJECT_DIR/ui/model.py" \
    "$INSTALL_UI_DIR/model.py"

install -Dm644 \
    "$PROJECT_DIR/ui/view.py" \
    "$INSTALL_UI_DIR/view.py"

install -Dm644 \
    "$PROJECT_DIR/ui/controller.py" \
    "$INSTALL_UI_DIR/controller.py"

# ------------------------------------------------------------
# Create UI launcher
# ------------------------------------------------------------

echo "[5/8] Installing UI launcher..."

cat > /usr/bin/ddc-monitor <<EOF
#!/bin/bash

exec /usr/bin/python3 "$INSTALL_UI_DIR/main.py"
EOF

chmod 755 /usr/bin/ddc-monitor

# ------------------------------------------------------------
# Install D-Bus files
# ------------------------------------------------------------

echo "[6/8] Installing D-Bus configuration..."

install -Dm644 \
    "$PROJECT_DIR/dbus/org.example.DDCMonitor.conf" \
    "$DBUS_POLICY_DIR/org.example.DDCMonitor.conf"

# Create the D-Bus activation file with the
# installed daemon path.

cat > "$DBUS_SERVICE_DIR/org.example.DDCMonitor.service" <<EOF
[D-BUS Service]
Name=org.example.DDCMonitor
Exec=/usr/bin/python3 $INSTALL_DAEMON_DIR/service.py
User=root
EOF

chmod 644 "$DBUS_SERVICE_DIR/org.example.DDCMonitor.service"

# ------------------------------------------------------------
# Install desktop entry
# ------------------------------------------------------------

echo "[7/8] Installing desktop entry..."

cat > "$APPLICATION_DIR/ddc-monitor.desktop" <<EOF
[Desktop Entry]
Name=DDC Monitor
Comment=Control monitor brightness and contrast
Exec=/usr/bin/ddc-monitor
Icon=video-display
Terminal=false
Type=Application
Categories=Settings;HardwareSettings;
StartupNotify=true
EOF

chmod 644 "$APPLICATION_DIR/ddc-monitor.desktop"

# ------------------------------------------------------------
# Optional systemd service
# ------------------------------------------------------------

if [ -f "$PROJECT_DIR/systemd/ddc-monitor.service" ]; then

    echo "      Installing systemd service..."

    install -Dm644 \
        "$PROJECT_DIR/systemd/ddc-monitor.service" \
        "$SYSTEMD_DIR/ddc-monitor.service"

    systemctl daemon-reload

fi

# ------------------------------------------------------------
# Reload D-Bus
# ------------------------------------------------------------

echo "      Reloading D-Bus configuration..."

systemctl reload dbus 2>/dev/null || true

# ------------------------------------------------------------
# Update desktop database if available
# ------------------------------------------------------------

if command -v update-desktop-database >/dev/null 2>&1; then

    update-desktop-database \
        "$APPLICATION_DIR" \
        >/dev/null 2>&1 || true

fi

# ------------------------------------------------------------
# Installation complete
# ------------------------------------------------------------

echo
echo "=========================================="
echo "      Installation completed"
echo "=========================================="
echo
echo "Installed UI:"
echo "    /usr/share/ddc-monitor/ui/"
echo
echo "Installed daemon:"
echo "    /usr/lib/ddc-monitor/"
echo
echo "Launcher:"
echo "    /usr/bin/ddc-monitor"
echo
echo "Desktop entry:"
echo "    /usr/share/applications/ddc-monitor.desktop"
echo
echo "D-Bus policy:"
echo "    /etc/dbus-1/system.d/org.example.DDCMonitor.conf"
echo
echo "D-Bus service:"
echo "    /usr/share/dbus-1/system-services/org.example.DDCMonitor.service"
echo
echo "You can start the application with:"
echo
echo "    ddc-monitor"
echo
echo "or search for 'DDC Monitor' in the GNOME application menu."
echo
