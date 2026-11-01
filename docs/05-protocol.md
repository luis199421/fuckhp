# 5. USB protocol

The printer enumerates as a USB CDC-ACM device (a "serial port"), VID
`0x1209` PID `0x0001`, product string `FreeJet FJ-1`, serial number = the
Pico's unique ID. Baud rate settings are ignored. Everything is binary
frames, little-endian. Reference implementations:
[`host/freejet/protocol.py`](../host/freejet/protocol.py) and
[`firmware/src/frame.c`](../firmware/src/frame.c) /
[`fj_proto.h`](../firmware/src/fj_proto.h).

## Frame

| Offset | Size | Field |
|---|---|---|
| 0 | 2 | magic `"FJ"` |
| 2 | 1 | type |
| 3 | 1 | seq (host chooses; echoed in ACK) |
| 4 | 4 | payload length N (≤ 16384) |
| 8 | N | payload |
| 8+N | 2 | CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF) over bytes 2 … 8+N−1 |

Bad CRC or garbage → the receiver drops one byte and re-synchronises on the
next `"FJ"`.

## Flow control

The printer only reads a frame's payload once it has room for it (ring
buffer for pass data, 32-entry queue for commands). Until then the USB
endpoint NAKs and the host's `write()` simply blocks. No credits or polling
needed; a host just writes the job stream.

The printer acknowledges every frame except `SWATH_DATA` with an `ACK`
(code 0 = accepted into the queue). Execution progress comes as `EVENT`s.

## Host → printer

| Type | Name | Payload | Notes |
|---|---|---|---|
| 0x01 | HELLO | – | → INFO |
| 0x02 | GET_STATUS | – | → STATUS |
| 0x10 | JOB_BEGIN | u8 flags (bit0 = roll), 3 pad | homes, checks the cartridge, powers the head |
| 0x11 | PAGE_BEGIN | u32 page_length_um (roll), u32 flags | spits, then loads a sheet (waits for the user) |
| 0x12 | SWATH_BEGIN | i32 y_um, i16 x0, u16 ncols, u8 dir, u8 flags (bit0 PackBits), u16 pad, u32 data_len | one pass |
| 0x13 | SWATH_DATA | bytes | chunks of the pass data until data_len is reached |
| 0x14 | PAGE_END | u8 flags (bit0 = pause for cutting) | ejects (sheet) / feeds to the tear edge (roll) |
| 0x15 | JOB_END | – | parks + caps, head power off |
| 0x16 | FEED | i32 µm | |
| 0x20 | PARAM_GET | u16 id | → PARAM |
| 0x21 | PARAM_SET | u16 id, u16 pad, i32 value | RAM only |
| 0x22 | PARAM_SAVE | – | write all params to flash |
| 0x23 | PARAM_DEFAULTS | – | |
| 0x30 | HOME | – | |
| 0x31 | PARK | – | |
| 0x32 | SPIT | u16 count | fire all nozzles into the spittoon |
| 0x33 | MOTORS_OFF | – | |
| 0x34 | MOVE_X | i32 µm | |
| 0x35 | NOZZLE_FIRE | u16 nozzle (0xFFFF = all), u16 count | in place, for diagnostics |
| 0x3F | ABORT | – | immediate: stops everything, flushes the queue |
| 0x7F | BOOTSEL | – | reboot into the RP2350 USB bootloader |

### Pass data

* `y_um`: paper position (µm from the leading edge) under swath row 0. Must
  never decrease within a page (the paper can't go backwards).
* Row 0 is the row under the nozzle closest to the paper exit. The
  firmware maps rows to physical nozzles; hosts never need the HP45 map.
* `x0`, `ncols`: pixel columns (1/600 in) from the paper's left edge.
* `dir`: 0 = carriage moves left→right, 1 = right→left.
* Data = for each column **in the order the carriage meets them**, 38 bytes:
  row *r* is bit *r % 8* (LSB first) of byte *r / 8*. Then PackBits-compressed
  if flags bit 0 is set.

## Printer → host

| Type | Name | Payload |
|---|---|---|
| 0x80 | ACK | u8 seq, u8 type, u16 code |
| 0x81 | INFO | u16 proto, u16 fw, char model[16], u32 ring_bytes, u16 dpi, u16 rows, u16 max_cols, u16 max_payload |
| 0x82 | STATUS | u8 state, u8 flags, u16 error, u16 tsr, u16 vhd_mv, u32 ring_free, u8 queue_len, u8 last_event, u16 pages, i32 paper_y_um, i32 x_um |
| 0x83 | EVENT | u8 code, u8 pad, u16 arg, i32 value |
| 0x84 | PARAM | u16 id, u16 pad, i32 value |

States: 0 idle, 1 busy, 2 printing, 3 waiting for paper, 4 waiting for the
button, 5 error. Flags: homed, paper, head, head_power, motors, job,
wait_paper, wait_button (bit 0 … 7).

Events: 1 paper needed, 2 paper loaded, 3 page done (value = page count),
4 job done, 5 error (arg = error code), 6 cut now, 7 head hot (pausing),
8 aborted.

Error codes: see `ERRORS` in `protocol.py` (1 bad CRC … 21 too fast). After
an error the printer rejects the rest of that job's frames until the next
`JOB_BEGIN` or `ABORT`.

Parameters: see [`host/freejet/params.py`](../host/freejet/params.py)
(generates the firmware's table).
