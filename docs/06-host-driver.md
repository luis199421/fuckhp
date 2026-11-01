# 6. Driver and printing software

The printer is a USB serial device, so **no kernel driver is ever needed**.
The "driver" is the `freejet` Python package in [`host/`](../host):

* `freejet` command-line tool: print PDFs, images and text files, preview,
  calibrate, maintain. Works on Linux, macOS and Windows.
* CUPS integration (Linux, and macOS with some care): a PPD, the
  `rastertofreejet` filter and the `freejet` backend, so the printer appears
  in every application's Print dialog.

## Command-line tool (all systems)

```bash
pip install "./host[pdf]"
```

```bash
freejet list                         # attached printers
freejet status
freejet print report.pdf             # Letter by default
freejet print photo.jpg --paper a4 --dither fs
freejet print notes.txt --pages 1-2 --copies 3
freejet print label.png --paper roll --length 100
freejet preview report.pdf -o preview.png   # exactly what would be printed
```

When a page starts the printer waits for paper: slide a sheet face up into
the rear slot along the left guide until the rollers take it.

On Windows the port is detected automatically (it appears as "USB Serial
Device (COMx)"). On Linux add yourself to the `dialout` group or install the
udev rule from `host/cups/install.sh`.

## CUPS (Linux)

```bash
sudo apt install cups python3-venv     # Debian/Ubuntu; other distros: cups + python3
sudo host/cups/install.sh --add
```

This installs the package into `/opt/freejet/venv`, the filter and backend
into CUPS, the PPD, and adds a queue called **FreeJet** for the connected
printer (URI `freejet://FJ-1?serial=…`). Then print from any application, or:

```bash
lp -d FreeJet document.pdf
lp -d FreeJet -o media=A4 -o FJDither=FS photo.jpg
lp -d FreeJet -o FJMediaSource=Roll -o media=Roll6 label.pdf
```

Options in the print dialog: paper size, paper source (sheet/roll),
pause-for-cutting (roll), bidirectional on/off, halftoning (auto, error
diffusion, ordered, black & white).

How it works: CUPS turns the document into 600 dpi 8-bit grey raster (using
Ghostscript); `rastertofreejet` halftones it, cuts it into passes and
compresses them; the `freejet` backend streams that to the printer and
reports "out of paper", errors and progress back to CUPS.

## macOS

The `freejet` tool works as-is (`pip install "./host[pdf]"`). For the Print
dialog, CUPS on macOS only loads filters/backends from system-protected
folders; copy the PPD, filter and backend by hand (`/Library/Printers/PPDs/`,
`/usr/libexec/cups/filter`, `/usr/libexec/cups/backend`) with SIP rules
permitting, or use the CLI / "Print to PDF" + `freejet print`. A driverless
(IPP Everywhere) printer application is on the roadmap.

## Windows

Use the `freejet` tool, e.g. "Print to PDF" then `freejet print file.pdf`.
A Windows print queue is on the roadmap (an IPP Everywhere printer
application would make Windows, macOS, iOS and Android print to it without
any driver).

## Firmware updates

```bash
freejet bootsel          # printer reboots as a USB drive (RP2350)
# copy firmware/build/freejet.uf2 onto the drive; it reboots by itself
```

## Python API

```python
from freejet.raster import PageSetup, load_pages
from freejet.job import job_frames
from freejet.transport import Printer

pages = load_pages("doc.pdf", PageSetup(paper="a4"))
with Printer() as p:
    p.stream(job_frames(pages, bidirectional=True), progress=print)
```

`freejet.emulator.VirtualPrinter` speaks the same protocol in software;
the test-suite (`pytest host/tests`) uses it, plus a C build of the
firmware's data path, to check every page byte-for-byte.
