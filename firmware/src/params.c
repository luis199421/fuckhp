#include "params.h"
#include <string.h>
#include "fj_proto.h"
#include "hardware/flash.h"
#include "hardware/sync.h"
#include "pico/flash.h"

int32_t g_param[P_COUNT];

typedef struct { uint16_t id; int32_t def, min, max; } meta_t;
#define FJ_P_META(id, NAME, def, mn, mx) {id, def, mn, mx},
static const meta_t meta[P_COUNT] = { FJ_PARAMS(FJ_P_META) };

void params_defaults(void) {
    for (int i = 0; i < P_COUNT; i++) g_param[i] = meta[i].def;
}

int params_index(uint16_t id) {
    for (int i = 0; i < P_COUNT; i++) if (meta[i].id == id) return i;
    return -1;
}

int params_set(uint16_t id, int32_t v) {
    int i = params_index(id);
    if (i < 0) return FJ_E_UNKNOWN_PARAM;
    if (v < meta[i].min || v > meta[i].max) return FJ_E_BAD_ARG;
    g_param[i] = v;
    return FJ_OK;
}

// ---- flash storage: last sector, stored as (id, value) pairs so the table can grow
#define STORE_OFFSET (PICO_FLASH_SIZE_BYTES - FLASH_SECTOR_SIZE)
#define STORE_MAGIC  0x464A5052u   // "FJPR"
typedef struct { uint16_t id; uint16_t pad; int32_t value; } entry_t;
typedef struct { uint32_t magic, count; entry_t e[96]; uint32_t crc; } store_t;
_Static_assert(sizeof(store_t) <= FLASH_SECTOR_SIZE, "store fits a sector");

static uint32_t crc32(const void *d, uint32_t n) {
    const uint8_t *p = d;
    uint32_t c = 0xFFFFFFFFu;
    while (n--) { c ^= *p++; for (int k = 0; k < 8; k++) c = (c >> 1) ^ (0xEDB88320u & -(c & 1)); }
    return ~c;
}

bool params_load(void) {
    params_defaults();
    const store_t *s = (const store_t *)(XIP_BASE + STORE_OFFSET);
    if (s->magic != STORE_MAGIC || s->count > 96) return false;
    if (s->crc != crc32(s, offsetof(store_t, crc))) return false;
    for (uint32_t i = 0; i < s->count; i++) params_set(s->e[i].id, s->e[i].value);
    return true;
}

static store_t pending;   // static: too big for the stack, must stay valid during the write

static void do_write(void *arg) {
    (void)arg;
    flash_range_erase(STORE_OFFSET, FLASH_SECTOR_SIZE);
    // program whole pages
    static uint8_t page[FLASH_SECTOR_SIZE];
    memset(page, 0xFF, sizeof page);
    memcpy(page, &pending, sizeof pending);
    flash_range_program(STORE_OFFSET, page, (sizeof pending + FLASH_PAGE_SIZE - 1) & ~(FLASH_PAGE_SIZE - 1));
}

bool params_save(void) {
    memset(&pending, 0, sizeof pending);
    pending.magic = STORE_MAGIC;
    pending.count = P_COUNT;
    for (int i = 0; i < P_COUNT; i++) { pending.e[i].id = meta[i].id; pending.e[i].value = g_param[i]; }
    pending.crc = crc32(&pending, offsetof(store_t, crc));
    // pauses core1 (it registered as a lockout victim) and interrupts during the write
    return flash_safe_execute(do_write, NULL, 1000) == PICO_OK;
}
