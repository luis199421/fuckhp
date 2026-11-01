#!/bin/sh
# Share a USB-connected FreeJet on the network from the Linux computer it's plugged into
# (Debian/Ubuntu/Raspberry Pi OS). Afterwards phones (AirPrint / Android default print
# service), Windows, macOS and Linux find the printer on the network with no driver.
#
#   sudo ./setup-print-server.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }

echo "-> packages"
apt-get update -q
apt-get install -y -q cups cups-filters ghostscript avahi-daemon python3-venv

echo "-> FreeJet driver + queue"
lpstat -p FreeJet >/dev/null 2>&1 || "$HERE/install.sh" --add

echo "-> share the queue on the network"
lpadmin -p FreeJet -o printer-is-shared=true
cupsctl --share-printers --remote-any
# let the user who ran sudo manage printers from the web UI (http://<host>:631)
[ -n "$SUDO_USER" ] && usermod -aG lpadmin "$SUDO_USER" 2>/dev/null || true
systemctl enable --now avahi-daemon cups
systemctl restart cups

IP=$(hostname -I | awk '{print $1}')
echo
echo "Done. The printer is shared as 'FreeJet' (advertised with Bonjour/mDNS)."
echo "  phones / macOS / Linux: it should just appear in the print dialog"
echo "  Windows: Settings > Printers > Add device, or add by address:"
echo "           http://$IP:631/printers/FreeJet"
echo "  web admin: http://$IP:631"
