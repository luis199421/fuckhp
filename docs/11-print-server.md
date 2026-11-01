# 11. Optional: print from phones and other computers over the network

The printer itself stays a **Pico 2-only USB printer**: no Raspberry Pi, no
Wi-Fi chip, nothing extra to buy. (Openprinter puts a Raspberry Pi Zero W
*inside* the printer to run CUPS. FreeJet keeps that job on a computer you
already own, which keeps the bill of materials down.)

```
 phone / laptop ──network (IPP, Bonjour)──► your Linux PC: CUPS + FreeJet driver ──USB──► FJ-1 (Pico 2)
```

## Share from the Linux computer the printer is plugged into

After `sudo host/cups/install.sh --add` (see [`06-host-driver.md`](06-host-driver.md)):

```bash
sudo host/cups/setup-print-server.sh
```

It installs Avahi (Bonjour), marks the **FreeJet** queue as shared and lets
CUPS accept jobs from the network. The computer has to be on for others to
print, like any shared printer.

## Printing from other devices

* **iPhone/iPad, macOS:** the printer appears in the print sheet (AirPrint,
  via CUPS's shared IPP queue).
* **Android:** the built-in Default Print Service finds IPP printers on the
  network.
* **Windows 10/11:** *Settings → Bluetooth & devices → Printers → Add device*,
  or *Add manually* with `http://<computer-address>:631/printers/FreeJet`;
  Windows uses its built-in IPP class driver.
* **Other Linux machines:** appear automatically (cups-browsed) or add the
  same IPP URL.

Paper size, roll and halftoning defaults are set in the CUPS web interface
(`http://<computer-address>:631`, Printers → FreeJet → Set Default Options);
phones use those defaults.

## Want it standalone, without a PC left on?

The same script runs unchanged on any small always-on Linux box you may
already have (an old Raspberry Pi, a home server, a NAS that runs Debian).
That is optional; the printer doesn't need it.

> Not yet tested on hardware: this is standard CUPS printer sharing, but
> phone and Windows compatibility with this queue should be confirmed on the
> first build.
