#!/bin/sh
# Turn a Raspberry Pi (Zero 2 W or any Pi on Raspberry Pi OS / Debian) into a Wi-Fi print
# server for a FreeJet connected to it by USB. Afterwards phones (AirPrint / Android default
# print service), Windows, macOS and Linux find the printer on the network with no driver.
#
#   sudo ./setup-print-server.sh
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)"; exit 1; }

echo "-> packages"
apt-get update -q
apt-get install -y -q cups cups-filters ghostscript avahi-daemon python3-venv

echo "-> FreeJet driver + queue"
"$HERE/install.sh" --add

echo "-> share the queue on the network"
lpadmin -p FreeJet -o printer-is-shared=true
cupsctl --share-printers --remote-any
# let the default user manage printers from the web UI (http://<pi>:631)
SUDO_USER_NAME=${SUDO_USER:-pi}
usermod -aG lpadmin "$SUDO_USER_NAME" 2>/dev/null || true
systemctl enable --now avahi-daemon cups
systemctl restart cups

IP=$(hostname -I | awk '{print $1}')
echo
echo "Done. The printer is shared as 'FreeJet' (advertised with Bonjour/mDNS)."
echo "  phones / macOS / Linux: it should just appear in the print dialog"
echo "  Windows: Settings > Printers > Add device, or add by address:"
echo "           http://$IP:631/printers/FreeJet"
echo "  web admin: http://$IP:631"
