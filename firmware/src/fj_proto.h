// FreeJet wire protocol constants. Mirrors host/freejet/protocol.py.
// See docs/05-protocol.md for the full description.
#pragma once
#include <stdint.h>

#define FJ_PROTO_VERSION 2
#define FJ_FW_VERSION    0x0200      // major << 8 | minor
#define FJ_MAX_PAYLOAD   16384
#define FJ_HEADER_SIZE   8
#define FJ_DPI           600
#define FJ_ROWS_K        324     // rows per pass, black cartridge only
#define FJ_ROWS_COLOR    168     // rows per pass when the colour cartridge is used
#define FJ_COL_BYTES     42      // bytes per pixel column per plane (336 bits)
#define FJ_MAX_PLANES    4
#define FJ_UM_PER_COL    (25400.0f / FJ_DPI)

enum {
    FJ_HELLO = 0x01, FJ_GET_STATUS = 0x02,
    FJ_JOB_BEGIN = 0x10, FJ_PAGE_BEGIN = 0x11, FJ_SWATH_BEGIN = 0x12, FJ_SWATH_DATA = 0x13,
    FJ_PAGE_END = 0x14, FJ_JOB_END = 0x15, FJ_FEED = 0x16,
    FJ_PARAM_GET = 0x20, FJ_PARAM_SET = 0x21, FJ_PARAM_SAVE = 0x22, FJ_PARAM_DEFAULTS = 0x23,
    FJ_HOME = 0x30, FJ_PARK = 0x31, FJ_SPIT = 0x32, FJ_MOTORS_OFF = 0x33, FJ_MOVE_X = 0x34,
    FJ_NOZZLE_FIRE = 0x35, FJ_ABORT = 0x3F, FJ_BOOTSEL = 0x7F,
    // device -> host
    FJ_ACK = 0x80, FJ_INFO = 0x81, FJ_STATUS = 0x82, FJ_EVENT = 0x83, FJ_PARAM = 0x84, FJ_LOG = 0x85,
};

enum { FJ_JOB_ROLL = 0x01 };
enum { FJ_SWATH_PACKBITS = 0x01 };
enum { FJ_PAGE_END_CUT_PAUSE = 0x01 };

enum {
    FJ_ST_IDLE = 0, FJ_ST_BUSY = 1, FJ_ST_PRINTING = 2, FJ_ST_WAIT_PAPER = 3,
    FJ_ST_WAIT_BUTTON = 4, FJ_ST_ERROR = 5,
};

enum {
    FJ_FL_HOMED = 1 << 0, FJ_FL_PAPER = 1 << 1, FJ_FL_HEAD = 1 << 2, FJ_FL_HEAD_POWER = 1 << 3,
    FJ_FL_MOTORS = 1 << 4, FJ_FL_JOB = 1 << 5, FJ_FL_WAIT_PAPER = 1 << 6, FJ_FL_WAIT_BUTTON = 1 << 7,
};

enum {
    FJ_EV_PAPER_NEEDED = 1, FJ_EV_PAPER_LOADED, FJ_EV_PAGE_DONE, FJ_EV_JOB_DONE, FJ_EV_ERROR,
    FJ_EV_CUT_NOW, FJ_EV_HEAD_HOT, FJ_EV_ABORTED,
};

enum {
    FJ_OK = 0, FJ_E_CRC, FJ_E_FRAME, FJ_E_UNKNOWN_CMD, FJ_E_BAD_ARG, FJ_E_BUSY, FJ_E_NO_HEAD,
    FJ_E_NOT_HOMED, FJ_E_HOME_FAILED, FJ_E_RANGE, FJ_E_SWATH_TOO_BIG, FJ_E_UNDERRUN,
    FJ_E_PAPER_JAM, FJ_E_HEAD_HOT, FJ_E_NO_VHD, FJ_E_ABORTED, FJ_E_FLASH, FJ_E_QUEUE_FULL,
    FJ_E_BACKFEED, FJ_E_NO_JOB, FJ_E_UNKNOWN_PARAM, FJ_E_TOO_FAST, FJ_E_INKSET, FJ_E_SHEET_END,
};

#pragma pack(push, 1)
typedef struct { uint16_t proto, fw; char model[16]; uint32_t ring_bytes;
                 uint16_t dpi, rows, max_cols, max_payload; } fj_info_t;   // rows = black-only pass
typedef struct { uint8_t state, flags; uint16_t error, tsr, vhd_mv; uint32_t ring_free;
                 uint8_t queue_len, last_event; uint16_t pages; int32_t paper_y_um, x_um; } fj_status_t;
typedef struct { uint8_t code, pad; uint16_t arg; int32_t value; } fj_event_t;
typedef struct { uint8_t seq, type; uint16_t code; } fj_ack_t;
typedef struct { uint16_t id, pad; int32_t value; } fj_param_t;
typedef struct { int32_t y_um; int16_t x0; uint16_t ncols; uint8_t dir, flags;
                 uint16_t pad; uint32_t data_len; } fj_swath_begin_t;
#pragma pack(pop)

_Static_assert(sizeof(fj_info_t) == 32, "info size");
_Static_assert(sizeof(fj_status_t) == 24, "status size");
_Static_assert(sizeof(fj_swath_begin_t) == 16, "swath size");
_Static_assert(sizeof(fj_event_t) == 8, "event size");
