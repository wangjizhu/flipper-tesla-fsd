#ifndef _SPI_LIB_H_
#define _SPI_LIB_H_

#include <furi_hal.h>
#include <furi_hal_bus.h>
#include <furi_hal_spi.h>
#include <furi_hal_spi_config.h>

#define TIMEOUT_SPI 100

// Use the firmware's built-in external SPI bus handle directly.
// It already has the correct pins (PA4=CS, PB3=SCK, PA7=MOSI, PA6=MISO)
// and is properly registered with the SPI bus mutex system.
// Do NOT allocate your own FuriHalSpiBusHandle — it causes
// null_pointer_dereference because the firmware's acquire/release
// expects handles to be part of its managed lifecycle.

// FUNCTIONS
// Returns a pointer to the firmware's pre-configured external SPI handle.
// No allocation needed — it's a firmware global.
FuriHalSpiBusHandle* spi_alloc(void);

#endif
