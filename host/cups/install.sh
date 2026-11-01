#!/bin/sh
# Install the FreeJet driver into CUPS (Linux; macOS see docs/06-host-driver.md).
#   sudo ./install.sh            install filter, backend, PPD and the python package
#   sudo ./install.sh --add      ...and add the first connected printer as queue "FreeJet"
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }

CUPS_LIB=$(cups-config --serverbin 2>/dev/null || echo /usr/lib/cups)
MODEL_DIR=/usr/share/cups/model/freejet

echo "-> python package into /opt/freejet/venv"
python3 -m venv /opt/freejet/venv
/opt/freejet/venv/bin/pip install -q --upgrade pip
/opt/freejet/venv/bin/pip install -q "$HERE/..[pdf]"
ln -sf /opt/freejet/venv/bin/freejet /usr/local/bin/freejet

echo "-> CUPS filter, backend and PPD ($CUPS_LIB)"
install -m 0755 "$HERE/rastertofreejet" "$CUPS_LIB/filter/rastertofreejet"
install -m 0700 "$HERE/freejet-backend" "$CUPS_LIB/backend/freejet"   # 0700: runs as root
install -d "$MODEL_DIR"
install -m 0644 "$HERE/freejet.ppd" "$MODEL_DIR/freejet.ppd"

echo "-> udev rule so normal users can run the freejet tool"
cat > /etc/udev/rules.d/70-freejet.rules <<'RULE'
SUBSYSTEM=="tty", ATTRS{idVendor}=="1209", ATTRS{idProduct}=="0001", ATTRS{product}=="FreeJet*", MODE="0666", SYMLINK+="freejet%n"
RULE
udevadm control --reload-rules 2>/dev/null || true

if command -v systemctl >/dev/null; then systemctl restart cups || true; fi

if [ "$1" = "--add" ]; then
    URI=$("$CUPS_LIB/backend/freejet" | head -n1 | awk '{print $2}')
    [ -n "$URI" ] || { echo "no printer found on USB - plug it in and re-run with --add"; exit 1; }
    lpadmin -p FreeJet -E -v "$URI" -m freejet/freejet.ppd -D "FreeJet FJ-1" -L "USB"
    lpoptions -d FreeJet
    echo "added queue FreeJet -> $URI (now the default printer)"
fi
echo "done."
