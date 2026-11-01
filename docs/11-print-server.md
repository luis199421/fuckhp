# 11. Optional: Wi-Fi printing from phones and every computer

Openprinter's good idea is to run CUPS on a Raspberry Pi inside the printer, so
anything on the network can print to it. FreeJet can do the same with a
**Raspberry Pi Zero 2 W** (~$15). The FreeJet stays a simple USB printer; the
Pi runs exactly the same CUPS filter and backend as a Linux desktop and shares
the queue over Wi-Fi.

```
 phone / laptop ──Wi-Fi (IPP, Bonjour)──► Pi Zero 2 W: CUPS + FreeJet driver ──USB──► FJ-1
```

## Hardware

* Raspberry Pi Zero 2 W + micro-SD card (8 GB+).
* A micro-USB OTG cable from the Pi's **USB** (data) port to the Pico 2.
* Power: the Pi draws ~0.5 A at 5 V; take it from the main board's 5 V rail
  (the MP1584 module gives 3 A) into the Pi's 5 V pad / PWR port, or use its
  own USB charger. It fits in the electronics tray next to the main board.

## Software

1. Flash **Raspberry Pi OS Lite (64-bit)** with Raspberry Pi Imager; in its
   settings set the Wi-Fi network, a user name and enable SSH.
2. Copy this repository to the Pi (or `git clone` it there), then:

```bash
sudo host/cups/setup-print-server.sh
```

That installs CUPS, Avahi (Bonjour) and the FreeJet driver, adds the
**FreeJet** queue for the printer on USB and shares it.

## Printing

* **iPhone/iPad, macOS:** the printer appears in the print sheet (AirPrint,
  via CUPS's shared IPP queue).
* **Android:** the built-in Default Print Service finds IPP printers on the
  network.
* **Windows 10/11:** *Settings → Bluetooth & devices → Printers → Add device*,
  or *Add manually* with `http://<pi-address>:631/printers/FreeJet`; Windows
  uses its built-in IPP class driver.
* **Linux:** appears automatically (cups-browsed) or add the same IPP URL.

Paper-size, roll and halftoning options from the PPD are available in the
Pi's web interface (`http://<pi-address>:631`, Printers → FreeJet → Set
Default Options); phones use those defaults.

> Not yet tested on hardware: this is standard CUPS printer sharing, which is
> widely used with Pi print servers, but phone and Windows compatibility with
> this particular queue should be confirmed on the first build.
