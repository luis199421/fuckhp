// USB descriptors: one CDC-ACM interface ("virtual serial port"). Every desktop
// OS has a built-in driver for it, so the printer needs no kernel driver.
#include <string.h>
#include "pico/unique_id.h"
#include "tusb.h"

#define USB_VID 0x1209   // pid.codes
#define USB_PID 0x0001   // pid.codes shared test PID: request your own before distributing

static const tusb_desc_device_t dev = {
    .bLength = sizeof(tusb_desc_device_t),
    .bDescriptorType = TUSB_DESC_DEVICE,
    .bcdUSB = 0x0200,
    .bDeviceClass = TUSB_CLASS_MISC,
    .bDeviceSubClass = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol = MISC_PROTOCOL_IAD,
    .bMaxPacketSize0 = CFG_TUD_ENDPOINT0_SIZE,
    .idVendor = USB_VID,
    .idProduct = USB_PID,
    .bcdDevice = 0x0001,
    .iManufacturer = 1,
    .iProduct = 2,
    .iSerialNumber = 3,
    .bNumConfigurations = 1,
};

uint8_t const *tud_descriptor_device_cb(void) { return (uint8_t const *)&dev; }

enum { ITF_CDC = 0, ITF_CDC_DATA, ITF_TOTAL };
#define EP_NOTIF 0x81
#define EP_OUT   0x02
#define EP_IN    0x82
#define CONFIG_LEN (TUD_CONFIG_DESC_LEN + TUD_CDC_DESC_LEN)

static const uint8_t config[] = {
    TUD_CONFIG_DESCRIPTOR(1, ITF_TOTAL, 0, CONFIG_LEN, 0x00, 100),
    TUD_CDC_DESCRIPTOR(ITF_CDC, 4, EP_NOTIF, 8, EP_OUT, EP_IN, 64),
};

uint8_t const *tud_descriptor_configuration_cb(uint8_t index) { (void)index; return config; }

static const char *strings[] = {"", "FreeJet project", "FreeJet FJ-2", "", "FreeJet FJ-2 data"};

uint16_t const *tud_descriptor_string_cb(uint8_t index, uint16_t langid) {
    (void)langid;
    static uint16_t out[40];
    char serial[2 * PICO_UNIQUE_BOARD_ID_SIZE_BYTES + 1];
    const char *s;
    if (index == 0) { out[1] = 0x0409; out[0] = (TUSB_DESC_STRING << 8) | 4; return out; }
    if (index == 3) { pico_get_unique_board_id_string(serial, sizeof serial); s = serial; }
    else if (index < sizeof strings / sizeof strings[0]) s = strings[index];
    else return NULL;
    size_t n = strlen(s);
    if (n > 39) n = 39;
    for (size_t i = 0; i < n; i++) out[1 + i] = (uint8_t)s[i];
    out[0] = (uint16_t)((TUSB_DESC_STRING << 8) | (2 * n + 2));
    return out;
}
