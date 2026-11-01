#include "comm.h"
#include "pico/time.h"
#include "tusb.h"

static fj_framer_t framer;
static comm_accept_fn accept_cb;
static comm_frame_fn frame_cb;
static uint32_t last_rx_ms;

void comm_init(comm_accept_fn accept, comm_frame_fn handle) {
    accept_cb = accept;
    frame_cb = handle;
    fj_framer_init(&framer);
    tusb_init();
}

uint32_t comm_last_rx_ms(void) { return last_rx_ms; }
bool comm_connected(void) { return tud_cdc_connected(); }

void comm_task(void) {
    tud_task();
    fj_frame_t f;
    uint32_t used;
    // frames left over in the framer (after a resync) first
    while (fj_framer_push(&framer, NULL, 0, &used, &f)) frame_cb(&f);
    for (int guard = 0; guard < 64 && tud_cdc_available(); guard++) {
        uint8_t type;
        uint32_t len;
        // back-pressure: leave the payload in the USB FIFO (the host gets NAKed)
        // until we have room for it
        if (fj_framer_peek(&framer, &type, &len) && !accept_cb(type, len)) break;
        uint8_t tmp[512];
        uint32_t want = fj_framer_want(&framer);
        uint32_t n = tud_cdc_read(tmp, want < sizeof tmp ? want : sizeof tmp);
        if (!n) break;
        last_rx_ms = to_ms_since_boot(get_absolute_time());
        uint32_t off = 0;
        while (off < n) {
            bool got = fj_framer_push(&framer, tmp + off, n - off, &used, &f);
            off += used;
            if (got) frame_cb(&f);
            else break;
        }
    }
}

void comm_send(uint8_t type, const void *payload, uint32_t len) {
    if (!tud_cdc_connected()) return;
    static uint8_t buf[64 + FJ_HEADER_SIZE + 2];
    if (len > 64) return;
    uint32_t n = fj_frame_encode(buf, type, 0, payload, len);
    uint32_t off = 0;
    absolute_time_t until = make_timeout_time_ms(50);
    while (off < n && !time_reached(until)) {
        off += tud_cdc_write(buf + off, n - off);
        tud_cdc_write_flush();
        if (off < n) tud_task();
    }
}

void comm_ack(uint8_t seq, uint8_t type, uint16_t code) {
    fj_ack_t a = {seq, type, code};
    comm_send(FJ_ACK, &a, sizeof a);
}

void comm_event(uint8_t code, uint16_t arg, int32_t value) {
    fj_event_t e = {code, 0, arg, value};
    comm_send(FJ_EVENT, &e, sizeof e);
}
