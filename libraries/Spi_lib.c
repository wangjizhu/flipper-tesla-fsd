#include "Spi_lib.h"

// Return the firmware's pre-initialized external SPI bus handle.
// This handle is already set up by furi_hal_spi_config_init() at boot
// with the correct GPIO pins (PA4/PB3/PA7/PA6) and bus mutex.
// We cast away const because MCP2515 code stores it as non-const,
// but we never modify the handle itself.
FuriHalSpiBusHandle* spi_alloc(void) {
    return (FuriHalSpiBusHandle*)&furi_hal_spi_bus_handle_external;
}
